package com.agentjd.task;

import com.agentjd.agent.AgentClient;
import com.agentjd.entity.AiTask;
import com.agentjd.entity.AiTaskStatus;
import com.agentjd.mapper.AiTaskMapper;
import com.agentjd.security.UserContext;
import com.agentjd.security.UserContextHolder;
import com.agentjd.web.TraceContext;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.Map;

@Component
@RequiredArgsConstructor
public class AiTaskExecutor {
    private final AiTaskMapper aiTaskMapper;
    private final AgentClient agentClient;
    private final AiTaskSupport taskSupport;

    public ExecutionResult execute(String taskUuid) {
        AiTask task = findTask(taskUuid);
        if (task == null) {
            return ExecutionResult.NOT_FOUND;
        }
        if (isTerminal(task.getStatus())) {
            return ExecutionResult.ALREADY_FINISHED;
        }

        UserContextHolder.set(new UserContext(task.getUserId(), null));
        TraceContext.setTraceId(task.getTraceId());
        try {
            markRunning(task);
            Map<String, Object> output = agentClient.call(
                    task.getCapability(), task.getAction(), task.getTaskUuid(), taskSupport.input(task));
            task.setOutputJson(taskSupport.toJson(output));
            task.setStatus(AiTaskStatus.SUCCESS.getCode());
            task.setProgress(100);
            task.setErrorMsg(null);
            task.setFinishedAt(LocalDateTime.now());
            task.setUpdatedAt(LocalDateTime.now());
            aiTaskMapper.updateById(task);
            taskSupport.cache(task);
            return ExecutionResult.SUCCESS;
        } finally {
            UserContextHolder.clear();
            TraceContext.clear();
        }
    }

    public void markRetrying(String taskUuid, String message) {
        AiTask task = findTask(taskUuid);
        if (task == null || isTerminal(task.getStatus())) {
            return;
        }
        task.setStatus(AiTaskStatus.PENDING.getCode());
        task.setProgress(0);
        task.setErrorMsg(truncate(message, 1024));
        task.setFinishedAt(null);
        task.setUpdatedAt(LocalDateTime.now());
        aiTaskMapper.updateById(task);
        taskSupport.cache(task);
    }

    public void markFailed(String taskUuid, String message) {
        AiTask task = findTask(taskUuid);
        if (task == null || isTerminal(task.getStatus())) {
            return;
        }
        task.setStatus(AiTaskStatus.FAILED.getCode());
        task.setProgress(100);
        task.setErrorMsg(truncate(message, 1024));
        task.setFinishedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        aiTaskMapper.updateById(task);
        taskSupport.cache(task);
    }

    private void markRunning(AiTask task) {
        task.setStatus(AiTaskStatus.RUNNING.getCode());
        task.setProgress(10);
        task.setErrorMsg(null);
        if (task.getStartedAt() == null) {
            task.setStartedAt(LocalDateTime.now());
        }
        task.setUpdatedAt(LocalDateTime.now());
        aiTaskMapper.updateById(task);
        taskSupport.cache(task);
    }

    private AiTask findTask(String taskUuid) {
        return aiTaskMapper.selectOne(new LambdaQueryWrapper<AiTask>().eq(AiTask::getTaskUuid, taskUuid));
    }

    private boolean isTerminal(Integer status) {
        return status != null && (status.equals(AiTaskStatus.SUCCESS.getCode())
                || status.equals(AiTaskStatus.FAILED.getCode())
                || status.equals(AiTaskStatus.CANCELED.getCode()));
    }

    private String truncate(String value, int maxLength) {
        if (value == null || value.length() <= maxLength) {
            return value;
        }
        return value.substring(0, maxLength);
    }

    public enum ExecutionResult {
        SUCCESS,
        ALREADY_FINISHED,
        NOT_FOUND
    }
}
