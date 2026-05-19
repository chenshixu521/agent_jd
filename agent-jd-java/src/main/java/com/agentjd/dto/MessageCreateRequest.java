package com.agentjd.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.util.Map;

@Data
public class MessageCreateRequest {
    @NotBlank
    private String role;
    @NotBlank
    private String content;
    private String taskUuid;
    private Map<String, Object> metadata;
}
