package com.agentjd.task;

import com.agentjd.entity.AiTask;
import com.agentjd.entity.AiTaskStatus;
import com.agentjd.mapper.AiTaskMapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "agent.task-queue", name = "enabled", havingValue = "true", matchIfMissing = true)
public class AiTaskQueueRecovery {
    private final AiTaskMapper aiTaskMapper;
    private final AiTaskQueuePublisher publisher;
    private final AiTaskQueueProperties properties;
    private final AiTaskMetrics metrics;

    @Scheduled(fixedDelayString = "${agent.task-queue.recovery-interval-ms:30000}")
    public void republishOrphanedTasks() {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime pendingCutoff = now.minus(properties.getPendingRecoveryAge());
        LocalDateTime runningCutoff = now.minus(properties.getRunningRecoveryAge());
        LambdaQueryWrapper<AiTask> query = new LambdaQueryWrapper<AiTask>()
                .and(wrapper -> wrapper
                        .eq(AiTask::getStatus, AiTaskStatus.PENDING.getCode())
                        .lt(AiTask::getUpdatedAt, pendingCutoff)
                        .or()
                        .eq(AiTask::getStatus, AiTaskStatus.RUNNING.getCode())
                        .lt(AiTask::getUpdatedAt, runningCutoff))
                .orderByAsc(AiTask::getCreatedAt)
                .last("LIMIT " + properties.getBatchSize());
        for (AiTask task : aiTaskMapper.selectList(query)) {
            try {
                if (publisher.enqueueIfMissing(task.getTaskUuid())) {
                    metrics.recordRecovery(task);
                    log.info("Republished orphaned AI task, taskUuid={}, status={}", task.getTaskUuid(), task.getStatus());
                }
            } catch (Exception ex) {
                log.warn("Republish orphaned AI task failed, taskUuid={}, reason={}", task.getTaskUuid(), ex.getMessage());
            }
        }
    }
}
