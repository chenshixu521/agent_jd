package com.agentjd.task;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

@Data
@ConfigurationProperties(prefix = "agent.task-queue")
public class AiTaskQueueProperties {
    private boolean enabled = true;
    private String streamKey = "ai:task:queue";
    private String deadLetterStreamKey = "ai:task:dlq";
    private String group = "agent-jd-worker";
    private String consumerName;
    private String taskKeyPrefix = "ai:task:";
    private int batchSize = 5;
    private int maxAttempts = 3;
    private long pollBlockMs = 2000;
    private long pollDelayMs = 500;
    private long initialDelayMs = 1000;
    private long recoveryIntervalMs = 30000;
    private Duration retryDelay = Duration.ofSeconds(15);
    private Duration claimIdle = Duration.ofMinutes(10);
    private Duration lockTimeout = Duration.ofMinutes(12);
    private Duration markerTtl = Duration.ofHours(24);
    private Duration pendingRecoveryAge = Duration.ofSeconds(10);
    private Duration runningRecoveryAge = Duration.ofMinutes(20);
}
