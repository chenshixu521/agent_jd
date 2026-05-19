package com.agentjd.vo;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class MessageVO {
    private Long id;
    private Long conversationId;
    private String role;
    private String content;
    private String taskUuid;
    private Object metadata;
    private LocalDateTime createdAt;
}
