package com.agentjd.vo;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class AiTaskVO {
    private Long id;
    private String taskUuid;
    private String capability;
    private String action;
    private Long bizId;
    private Integer status;
    private Integer progress;
    private Object input;
    private Object output;
    private String errorMsg;
    private String traceId;
    private LocalDateTime createdAt;
    private LocalDateTime startedAt;
    private LocalDateTime finishedAt;
}
