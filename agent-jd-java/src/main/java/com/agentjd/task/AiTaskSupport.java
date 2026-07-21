package com.agentjd.task;

import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import com.agentjd.entity.AiTask;
import com.agentjd.vo.AiTaskVO;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class AiTaskSupport {
    private final ObjectMapper objectMapper;
    private final RedisTemplate<String, Object> redisTemplate;

    public void cache(AiTask task) {
        try {
            redisTemplate.opsForValue().set("ai:task:" + task.getTaskUuid(), toVO(task), Duration.ofHours(24));
        } catch (RuntimeException ex) {
            log.warn("Cache AI task failed, taskUuid={}, reason={}", task.getTaskUuid(), ex.getMessage());
        }
    }

    public AiTaskVO toVO(AiTask task) {
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

    public Map<String, Object> input(AiTask task) {
        if (task.getInputJson() == null || task.getInputJson().isBlank()) {
            return Map.of();
        }
        try {
            return objectMapper.readValue(task.getInputJson(), new TypeReference<>() {
            });
        } catch (JsonProcessingException ex) {
            throw new BizException(ErrorCode.PARAM_INVALID, "任务输入 JSON 解析失败");
        }
    }

    public String toJson(Object value) {
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
