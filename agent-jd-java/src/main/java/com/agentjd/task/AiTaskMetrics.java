package com.agentjd.task;

import com.agentjd.entity.AiTask;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Tags;
import io.micrometer.core.instrument.Timer;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Set;

@Component
@RequiredArgsConstructor
public class AiTaskMetrics {
    private static final Set<String> CAPABILITIES = Set.of(
            "resume", "jd", "keyword", "project", "match", "greeting", "chat");
    private static final Set<String> ACTIONS = Set.of(
            "optimize", "advice", "parse", "analyze", "extract", "rewrite", "generate", "message", "talk");

    private final MeterRegistry registry;

    public void recordSubmitted(AiTask task) {
        counter("agent.jd.tasks.submitted", "AI tasks accepted by the Java service", task).increment();
    }

    public void recordCompleted(AiTask task, String outcome) {
        Tags tags = taskTags(task).and("outcome", outcome);
        Counter.builder("agent.jd.tasks.completed")
                .description("AI tasks reaching a terminal state")
                .tags(tags)
                .register(registry)
                .increment();

        LocalDateTime started = task.getCreatedAt() != null ? task.getCreatedAt() : task.getStartedAt();
        LocalDateTime finished = task.getFinishedAt();
        if (started != null && finished != null && !finished.isBefore(started)) {
            Timer.builder("agent.jd.task.duration")
                    .description("AI task end-to-end duration from creation to terminal state")
                    .tags(tags)
                    .publishPercentileHistogram()
                    .register(registry)
                    .record(Duration.between(started, finished));
        }
    }

    public void recordRetry(AiTask task) {
        counter("agent.jd.task.retries", "AI task execution retries", task).increment();
    }

    public void recordDeadLetter(AiTask task) {
        counter("agent.jd.task.dlq", "AI tasks written to the dead letter stream", task).increment();
    }

    public void recordRecovery(AiTask task) {
        counter("agent.jd.task.recoveries", "Orphaned AI tasks republished by the recovery scanner", task).increment();
    }

    private Counter counter(String name, String description, AiTask task) {
        return Counter.builder(name)
                .description(description)
                .tags(taskTags(task))
                .register(registry);
    }

    private Tags taskTags(AiTask task) {
        return Tags.of(
                "capability", bounded(task.getCapability(), CAPABILITIES),
                "action", bounded(task.getAction(), ACTIONS));
    }

    private String bounded(String value, Set<String> allowed) {
        return value != null && allowed.contains(value) ? value : "other";
    }
}
