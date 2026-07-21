package com.agentjd.service.impl;

import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import com.agentjd.dto.AiTaskSubmitRequest;
import com.agentjd.entity.AiTask;
import com.agentjd.entity.AiTaskStatus;
import com.agentjd.mapper.AiTaskMapper;
import com.agentjd.service.AiTaskService;
import com.agentjd.task.AiTaskQueuePublisher;
import com.agentjd.task.AiTaskMetrics;
import com.agentjd.task.AiTaskSupport;
import com.agentjd.vo.AiTaskVO;
import com.agentjd.security.UserContextHolder;
import com.agentjd.web.TraceContext;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class AiTaskServiceImpl implements AiTaskService {
    private final AiTaskMapper aiTaskMapper;
    private final AiTaskQueuePublisher queuePublisher;
    private final AiTaskSupport taskSupport;
    private final AiTaskMetrics metrics;

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
        task.setInputJson(taskSupport.toJson(request.getInput()));
        task.setTraceId(traceId);
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        aiTaskMapper.insert(task);
        taskSupport.cache(task);
        enqueueAfterCommit(task);
        return detail(task.getTaskUuid());
    }

    private void enqueueAfterCommit(AiTask task) {
        Runnable enqueue = () -> {
            metrics.recordSubmitted(task);
            try {
                queuePublisher.enqueueIfMissing(task.getTaskUuid());
            } catch (Exception ex) {
                log.error("Enqueue AI task failed; recovery scanner will retry, taskUuid={}, reason={}",
                        task.getTaskUuid(), ex.getMessage(), ex);
            }
        };
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    enqueue.run();
                }
            });
        } else {
            enqueue.run();
        }
    }

    @Override
    public List<AiTaskVO> list() {
        return aiTaskMapper.selectList(new LambdaQueryWrapper<AiTask>()
                .eq(AiTask::getUserId, UserContextHolder.getUserId())
                .orderByDesc(AiTask::getCreatedAt))
                .stream().map(taskSupport::toVO).toList();
    }

    @Override
    public AiTaskVO detail(String taskUuid) {
        AiTask task = requireOwnTask(taskUuid);
        return taskSupport.toVO(task);
    }

    @Override
    public AiTaskVO result(String taskUuid) {
        return detail(taskUuid);
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
}
