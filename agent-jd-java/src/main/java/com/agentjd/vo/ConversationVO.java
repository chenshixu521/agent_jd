package com.agentjd.vo;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class ConversationVO {
    private Long id;
    private String title;
    private String scene;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
