package com.agentjd.task;

import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.RecordId;
import org.springframework.data.redis.core.StreamOperations;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;

import java.time.Duration;
import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AiTaskQueueWorkerTest {
    private StringRedisTemplate redisTemplate;
    private StreamOperations<String, Object, Object> streamOperations;
    private AiTaskQueuePublisher publisher;
    private AiTaskExecutor executor;
    private AiTaskQueueProperties properties;
    private AiTaskQueueWorker worker;

    @BeforeEach
    @SuppressWarnings("unchecked")
    void setUp() {
        redisTemplate = mock(StringRedisTemplate.class);
        streamOperations = mock(StreamOperations.class);
        publisher = mock(AiTaskQueuePublisher.class);
        executor = mock(AiTaskExecutor.class);
        properties = new AiTaskQueueProperties();
        properties.setConsumerName("test-worker");
        properties.setMaxAttempts(3);
        properties.setLockTimeout(Duration.ofMinutes(1));
        when(redisTemplate.opsForStream()).thenReturn(streamOperations);
        when(redisTemplate.execute(
                any(DefaultRedisScript.class),
                anyList(),
                anyString(),
                anyString())).thenReturn(1L);
        when(publisher.lockKey("task-1")).thenReturn("ai:task:task-1:lock");
        worker = new AiTaskQueueWorker(redisTemplate, properties, publisher, executor);
    }

    @Test
    void acknowledgesSuccessfulTask() {
        MapRecord<String, Object, Object> record = record();
        when(executor.execute("task-1")).thenReturn(AiTaskExecutor.ExecutionResult.SUCCESS);

        worker.handleRecord(record, 1);

        verify(streamOperations).acknowledge("ai:task:queue", "agent-jd-worker", record.getId());
        verify(streamOperations).delete("ai:task:queue", record.getId());
        verify(publisher).clearMarker("task-1");
    }

    @Test
    void leavesFailedMessagePendingForRetry() {
        MapRecord<String, Object, Object> record = record();
        when(executor.execute("task-1")).thenThrow(new IllegalStateException("temporary error"));

        worker.handleRecord(record, 1);

        verify(executor).markRetrying(eq("task-1"), anyString());
        verify(streamOperations, never()).acknowledge(anyString(), anyString(), any(RecordId.class));
        verify(publisher, never()).publishDeadLetter(anyString(), anyString(), eq(1), anyString());
    }

    @Test
    void movesTaskToDeadLetterQueueAfterMaxAttempts() {
        MapRecord<String, Object, Object> record = record();
        when(executor.execute("task-1")).thenThrow(new IllegalStateException("permanent error"));

        worker.handleRecord(record, 3);

        verify(publisher).publishDeadLetter("task-1", "1-0", 3, "permanent error");
        verify(executor).markFailed(eq("task-1"), anyString());
        verify(streamOperations).acknowledge("ai:task:queue", "agent-jd-worker", record.getId());
        verify(publisher).clearMarker("task-1");
    }

    @Test
    void movesNonRetryableTaskToDeadLetterQueueImmediately() {
        MapRecord<String, Object, Object> record = record();
        when(executor.execute("task-1"))
                .thenThrow(new BizException(ErrorCode.AGENT_CALL_FAILED, "authentication failed", false));

        worker.handleRecord(record, 1);

        verify(publisher).publishDeadLetter("task-1", "1-0", 1, "authentication failed");
        verify(executor).markFailed(eq("task-1"), anyString());
        verify(streamOperations).acknowledge("ai:task:queue", "agent-jd-worker", record.getId());
    }

    @Test
    void recognizesBusyGroupInNestedRedisException() {
        RuntimeException exception = new RuntimeException(
                "Error in execution",
                new RuntimeException("BUSYGROUP Consumer Group name already exists"));

        assertTrue(worker.isBusyGroup(exception));
    }

    @Test
    void reacquiresLockOwnedBySameConsumer() {
        assertTrue(worker.acquireLock("ai:task:task-1:lock"));

        verify(redisTemplate).execute(
                any(DefaultRedisScript.class),
                eq(List.of("ai:task:task-1:lock")),
                eq("test-worker"),
                eq("60000"));
    }

    private MapRecord<String, Object, Object> record() {
        return MapRecord.create("ai:task:queue", Map.<Object, Object>of("taskUuid", "task-1"))
                .withId(RecordId.of("1-0"));
    }
}
