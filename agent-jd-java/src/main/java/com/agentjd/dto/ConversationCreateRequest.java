package com.agentjd.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ConversationCreateRequest {
    @NotBlank
    private String title;
    private String scene;
}
