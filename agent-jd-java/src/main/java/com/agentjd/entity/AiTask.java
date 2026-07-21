package com.agentjd.entity;

import com.baomidou.mybatisplus.annotation.FieldStrategy;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("t_ai_task")
public class AiTask {
    @TableId
    private Long id;
    private String taskUuid;
    private Long userId;
    private String capability;
    private String action;
    private Long bizId;
    private Integer status;
    private Integer progress;
    private String inputJson;
    private String outputJson;
    @TableField(updateStrategy = FieldStrategy.ALWAYS)
    private String errorMsg;
    private String traceId;
    private LocalDateTime startedAt;
    private LocalDateTime finishedAt;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
