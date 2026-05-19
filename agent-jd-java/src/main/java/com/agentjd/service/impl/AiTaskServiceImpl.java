package com.agentjd.service.impl;

import com.agentjd.agent.AgentClient;
import com.agentjd.dto.AiTaskSubmitRequest;
import com.agentjd.entity.AiTask;
import com.agentjd.entity.AiTaskStatus;
import com.agentjd.mapper.AiTaskMapper;
import com.agentjd.vo.AiTaskVO;
import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import com.agentjd.security.UserContext;
import com.agentjd.security.UserContextHolder;
import com.agentjd.web.TraceContext;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import com.agentjd.service.AiTaskService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

@Service
@RequiredArgsConstructor
public class AiTaskServiceImpl implements AiTaskService {
    private final AiTaskMapper aiTaskMapper;
    private final AgentClient agentClient;
    private final ObjectMapper objectMapper;
    private final RedisTemplate<String, Object> redisTemplate;

    @Transactional(rollbackFor = Exception.class)
    @Override
    public AiTaskVO submit(AiTaskSubmitRequest request) {
        Long userId = UserContextHolder.getUserId();
        String traceId = TraceContext.getTraceId();
        AiTask task = new AiTask();
        task.setTaskUuid(UUID.randomUUID().toString());
        task.setUserId(userId);
        task.setCapability(request.getCapability());
        task.setAction(request.getAction());
        task.setBizId(request.getBizId());
        task.setStatus(AiTaskStatus.PENDING.getCode());
        task.setProgress(0);
        task.setInputJson(toJson(request.getInput()));
        task.setTraceId(traceId);
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        aiTaskMapper.insert(task);
        cacheTask(task);
        Map<String, Object> input = request.getInput() == null ? Map.of() : request.getInput();
        startAsyncAfterCommit(task, input, userId, traceId);
        return detail(task.getTaskUuid());
    }

    private void startAsyncAfterCommit(AiTask task, Map<String, Object> input, Long userId, String traceId) {
        Runnable worker = () -> CompletableFuture.runAsync(() -> processAsync(task, input, userId, traceId));
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    worker.run();
                }
            });
        } else {
            worker.run();
        }
    }

    private void processAsync(AiTask task, Map<String, Object> input, Long userId, String traceId) {
        UserContextHolder.set(new UserContext(userId, null));
        TraceContext.setTraceId(traceId);
        try {
            processSync(task, input);
        } finally {
            UserContextHolder.clear();
            TraceContext.clear();
        }
    }

    @Override
    public List<AiTaskVO> list() {
        return aiTaskMapper.selectList(new LambdaQueryWrapper<AiTask>()
                .eq(AiTask::getUserId, UserContextHolder.getUserId())
                .orderByDesc(AiTask::getCreatedAt))
                .stream().map(this::toVO).toList();
    }

    @Override
    public AiTaskVO detail(String taskUuid) {
        AiTask task = requireOwnTask(taskUuid);
        return toVO(task);
    }

    @Override
    public AiTaskVO result(String taskUuid) {
        return detail(taskUuid);
    }

    private void processSync(AiTask task, Map<String, Object> input) {
        task.setStatus(AiTaskStatus.RUNNING.getCode());
        task.setProgress(10);
        task.setStartedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        aiTaskMapper.updateById(task);
        cacheTask(task);
        try {
            Map<String, Object> output = agentClient.call(task.getCapability(), task.getAction(), task.getTaskUuid(),
                    input);
            task.setOutputJson(toJson(output));
            task.setStatus(AiTaskStatus.SUCCESS.getCode());
            task.setProgress(100);
            task.setFinishedAt(LocalDateTime.now());
            task.setUpdatedAt(LocalDateTime.now());
            aiTaskMapper.updateById(task);
            cacheTask(task);
        } catch (Exception ex) {
            task.setStatus(AiTaskStatus.FAILED.getCode());
            task.setProgress(100);
            task.setErrorMsg(ex.getMessage());
            task.setFinishedAt(LocalDateTime.now());
            task.setUpdatedAt(LocalDateTime.now());
            aiTaskMapper.updateById(task);
            cacheTask(task);
            throw ex;
        }
    }

    private AiTask requireOwnTask(String taskUuid) {
        AiTask task = aiTaskMapper.selectOne(new LambdaQueryWrapper<AiTask>()
                .eq(AiTask::getTaskUuid, taskUuid)
                .eq(AiTask::getUserId, UserContextHolder.getUserId()));
        if (task == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "AI 任务不存在");
        }
        return task;
    }

    private void cacheTask(AiTask task) {
        redisTemplate.opsForValue().set("ai:task:" + task.getTaskUuid(), toVO(task), Duration.ofHours(24));
    }

    private AiTaskVO toVO(AiTask task) {
        return AiTaskVO.builder()
                .id(task.getId())
                .taskUuid(task.getTaskUuid())
                .capability(task.getCapability())
                .action(task.getAction())
                .bizId(task.getBizId())
                .status(task.getStatus())
                .progress(task.getProgress())
                .input(fromJson(task.getInputJson()))
                .output(fromJson(task.getOutputJson()))
                .errorMsg(task.getErrorMsg())
                .traceId(task.getTraceId())
                .createdAt(task.getCreatedAt())
                .startedAt(task.getStartedAt())
                .finishedAt(task.getFinishedAt())
                .build();
    }

    private String toJson(Object value) {
        try {
            return value == null ? null : objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException ex) {
            throw new BizException(ErrorCode.PARAM_INVALID, "JSON 序列化失败");
        }
    }

    private Object fromJson(String json) {
        if (json == null || json.isBlank()) {
            return null;
        }
        try {
            return objectMapper.readValue(json, new TypeReference<Map<String, Object>>() {
            });
        } catch (JsonProcessingException ex) {
            return json;
        }
    }
}
