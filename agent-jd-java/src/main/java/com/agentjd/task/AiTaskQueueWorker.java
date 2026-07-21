package com.agentjd.task;

import com.agentjd.common.BizException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.data.domain.Range;
import org.springframework.data.redis.connection.stream.Consumer;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.PendingMessage;
import org.springframework.data.redis.connection.stream.PendingMessages;
import org.springframework.data.redis.connection.stream.ReadOffset;
import org.springframework.data.redis.connection.stream.RecordId;
import org.springframework.data.redis.connection.stream.StreamOffset;
import org.springframework.data.redis.connection.stream.StreamReadOptions;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Component
@ConditionalOnProperty(prefix = "agent.task-queue", name = "enabled", havingValue = "true", matchIfMissing = true)
public class AiTaskQueueWorker {
    private static final DefaultRedisScript<Long> ACQUIRE_LOCK_SCRIPT = new DefaultRedisScript<>("""
            local owner = redis.call('GET', KEYS[1])
            if not owner then
              redis.call('SET', KEYS[1], ARGV[1], 'PX', ARGV[2])
              return 1
            end
            if owner == ARGV[1] then
              redis.call('PEXPIRE', KEYS[1], ARGV[2])
              return 1
            end
            return 0
            """, Long.class);

    private static final DefaultRedisScript<Long> RELEASE_LOCK_SCRIPT = new DefaultRedisScript<>("""
            if redis.call('GET', KEYS[1]) == ARGV[1] then
              return redis.call('DEL', KEYS[1])
            end
            return 0
            """, Long.class);

    private final StringRedisTemplate stringRedisTemplate;
    private final AiTaskQueueProperties properties;
    private final AiTaskQueuePublisher publisher;
    private final AiTaskExecutor executor;
    private final String consumerName;
    private volatile boolean groupReady;

    public AiTaskQueueWorker(
            StringRedisTemplate stringRedisTemplate,
            AiTaskQueueProperties properties,
            AiTaskQueuePublisher publisher,
            AiTaskExecutor executor) {
        this.stringRedisTemplate = stringRedisTemplate;
        this.properties = properties;
        this.publisher = publisher;
        this.executor = executor;
        this.consumerName = resolveConsumerName(properties.getConsumerName());
    }

    @Scheduled(
            initialDelayString = "${agent.task-queue.initial-delay-ms:1000}",
            fixedDelayString = "${agent.task-queue.poll-delay-ms:500}")
    public void poll() {
        try {
            ensureGroup();
            if (recoverPending()) {
                return;
            }
            readNewMessages();
        } catch (Exception ex) {
            log.warn("AI task queue poll failed, reason={}", rootCauseMessage(ex));
        }
    }

    void handleRecord(MapRecord<String, Object, Object> record, int attempt) {
        Object taskUuidValue = record.getValue().get("taskUuid");
        String taskUuid = taskUuidValue == null ? null : String.valueOf(taskUuidValue);
        if (!StringUtils.hasText(taskUuid)) {
            acknowledge(record);
            return;
        }

        String lockKey = publisher.lockKey(taskUuid);
        if (!acquireLock(lockKey)) {
            return;
        }

        try {
            AiTaskExecutor.ExecutionResult result;
            try {
                result = executor.execute(taskUuid);
            } catch (Exception ex) {
                handleFailure(taskUuid, record, attempt, ex);
                return;
            }
            if (result == AiTaskExecutor.ExecutionResult.SUCCESS
                    || result == AiTaskExecutor.ExecutionResult.ALREADY_FINISHED
                    || result == AiTaskExecutor.ExecutionResult.NOT_FOUND) {
                acknowledge(record);
                publisher.clearMarker(taskUuid);
            }
        } finally {
            releaseLock(lockKey);
        }
    }

    private void handleFailure(String taskUuid, MapRecord<String, Object, Object> record, int attempt, Exception ex) {
        String message = errorMessage(ex);
        boolean retryable = !(ex instanceof BizException bizException) || bizException.isRetryable();
        if (retryable && attempt < properties.getMaxAttempts()) {
            executor.markRetrying(taskUuid, "第 " + attempt + " 次执行失败，将自动重试：" + message);
            log.warn("AI task will retry, taskUuid={}, attempt={}, reason={}", taskUuid, attempt, message);
            return;
        }

        try {
            publisher.publishDeadLetter(taskUuid, record.getId().getValue(), attempt, message);
            String failureMessage = retryable
                    ? "超过最大重试次数（" + properties.getMaxAttempts() + "）：" + message
                    : "不可重试错误：" + message;
            executor.markFailed(taskUuid, failureMessage);
            acknowledge(record);
            publisher.clearMarker(taskUuid);
            log.error("AI task moved to dead letter queue, taskUuid={}, attempts={}, reason={}", taskUuid, attempt, message);
        } catch (Exception deadLetterException) {
            log.error("AI task dead letter handling failed, taskUuid={}, reason={}", taskUuid,
                    deadLetterException.getMessage(), deadLetterException);
        }
    }

    private boolean recoverPending() {
        PendingMessages pending = stringRedisTemplate.opsForStream()
                .pending(properties.getStreamKey(), properties.getGroup(), Range.unbounded(), properties.getBatchSize());
        if (pending == null || pending.isEmpty()) {
            return false;
        }

        List<PendingMessage> eligible = new ArrayList<>();
        for (PendingMessage item : pending) {
            Duration threshold = consumerName.equals(item.getConsumerName())
                    ? properties.getRetryDelay()
                    : properties.getClaimIdle();
            if (!item.getElapsedTimeSinceLastDelivery().minus(threshold).isNegative()) {
                eligible.add(item);
            }
        }
        if (eligible.isEmpty()) {
            return false;
        }

        Map<String, Integer> attempts = new HashMap<>();
        RecordId[] ids = eligible.stream().map(PendingMessage::getId).toArray(RecordId[]::new);
        for (PendingMessage item : eligible) {
            attempts.put(item.getIdAsString(), Math.toIntExact(item.getTotalDeliveryCount()) + 1);
        }
        List<MapRecord<String, Object, Object>> claimed = stringRedisTemplate.opsForStream().claim(
                properties.getStreamKey(), properties.getGroup(), consumerName, Duration.ZERO, ids);
        for (MapRecord<String, Object, Object> record : claimed) {
            handleRecord(record, attempts.getOrDefault(record.getId().getValue(), 1));
        }
        return true;
    }

    @SuppressWarnings("unchecked")
    private void readNewMessages() {
        List<MapRecord<String, Object, Object>> records = stringRedisTemplate.opsForStream().read(
                Consumer.from(properties.getGroup(), consumerName),
                StreamReadOptions.empty()
                        .count(properties.getBatchSize())
                        .block(Duration.ofMillis(properties.getPollBlockMs())),
                StreamOffset.create(properties.getStreamKey(), ReadOffset.lastConsumed()));
        if (records == null) {
            return;
        }
        for (MapRecord<String, Object, Object> record : records) {
            handleRecord(record, 1);
        }
    }

    private void ensureGroup() {
        if (groupReady) {
            return;
        }
        RecordId bootstrapId = stringRedisTemplate.opsForStream().add(
                properties.getStreamKey(), Map.of("type", "bootstrap"));
        try {
            stringRedisTemplate.opsForStream().createGroup(
                    properties.getStreamKey(), ReadOffset.from("0-0"), properties.getGroup());
            log.info("Created AI task consumer group, stream={}, group={}", properties.getStreamKey(), properties.getGroup());
        } catch (Exception ex) {
            if (!isBusyGroup(ex)) {
                throw ex;
            }
        } finally {
            if (bootstrapId != null) {
                stringRedisTemplate.opsForStream().delete(properties.getStreamKey(), bootstrapId);
            }
        }
        groupReady = true;
    }

    boolean isBusyGroup(Throwable throwable) {
        Throwable current = throwable;
        while (current != null) {
            if (String.valueOf(current.getMessage()).contains("BUSYGROUP")) {
                return true;
            }
            current = current.getCause();
        }
        return false;
    }

    private void acknowledge(MapRecord<String, Object, Object> record) {
        stringRedisTemplate.opsForStream().acknowledge(
                properties.getStreamKey(), properties.getGroup(), record.getId());
        stringRedisTemplate.opsForStream().delete(properties.getStreamKey(), record.getId());
    }

    private void releaseLock(String lockKey) {
        stringRedisTemplate.execute(RELEASE_LOCK_SCRIPT, List.of(lockKey), consumerName);
    }

    boolean acquireLock(String lockKey) {
        Long result = stringRedisTemplate.execute(
                ACQUIRE_LOCK_SCRIPT,
                List.of(lockKey),
                consumerName,
                String.valueOf(properties.getLockTimeout().toMillis()));
        return Long.valueOf(1L).equals(result);
    }

    private String errorMessage(Exception ex) {
        String message = ex.getMessage();
        return StringUtils.hasText(message) ? message : ex.getClass().getSimpleName();
    }

    private String rootCauseMessage(Throwable throwable) {
        Throwable current = throwable;
        while (current.getCause() != null && current.getCause() != current) {
            current = current.getCause();
        }
        return StringUtils.hasText(current.getMessage()) ? current.getMessage() : current.getClass().getSimpleName();
    }

    private String resolveConsumerName(String configuredName) {
        if (StringUtils.hasText(configuredName)) {
            return configuredName;
        }
        String hostname = System.getenv("HOSTNAME");
        return StringUtils.hasText(hostname) ? hostname : "agent-jd-" + UUID.randomUUID();
    }
}
