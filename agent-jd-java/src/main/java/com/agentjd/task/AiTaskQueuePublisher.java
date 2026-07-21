package com.agentjd.task;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class AiTaskQueuePublisher {
    private static final DefaultRedisScript<Long> ENQUEUE_SCRIPT = new DefaultRedisScript<>("""
            if redis.call('EXISTS', KEYS[2]) == 1 then
              return 0
            end
            redis.call('XADD', KEYS[1], '*', 'taskUuid', ARGV[1], 'enqueuedAt', ARGV[2])
            redis.call('SET', KEYS[2], '1', 'PX', ARGV[3])
            return 1
            """, Long.class);

    private final StringRedisTemplate stringRedisTemplate;
    private final AiTaskQueueProperties properties;

    public boolean enqueueIfMissing(String taskUuid) {
        String markerKey = markerKey(taskUuid);
        Long result = stringRedisTemplate.execute(
                ENQUEUE_SCRIPT,
                List.of(properties.getStreamKey(), markerKey),
                taskUuid,
                Instant.now().toString(),
                String.valueOf(properties.getMarkerTtl().toMillis()));
        return Long.valueOf(1L).equals(result);
    }

    public void publishDeadLetter(String taskUuid, String recordId, int attempts, String error) {
        Map<String, String> fields = Map.of(
                "taskUuid", taskUuid,
                "sourceRecordId", recordId,
                "attempts", String.valueOf(attempts),
                "error", truncate(error, 1024),
                "failedAt", Instant.now().toString());
        stringRedisTemplate.opsForStream().add(properties.getDeadLetterStreamKey(), fields);
    }

    public void clearMarker(String taskUuid) {
        stringRedisTemplate.delete(markerKey(taskUuid));
    }

    public String lockKey(String taskUuid) {
        return properties.getTaskKeyPrefix() + taskUuid + ":lock";
    }

    private String markerKey(String taskUuid) {
        return properties.getTaskKeyPrefix() + taskUuid + ":queued";
    }

    private String truncate(String value, int maxLength) {
        if (value == null || value.length() <= maxLength) {
            return value == null ? "unknown" : value;
        }
        return value.substring(0, maxLength);
    }
}
