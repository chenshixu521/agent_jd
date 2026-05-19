package com.agentjd.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.util.Map;

@Data
public class AiTaskSubmitRequest {
    @NotBlank
    private String capability;
    @NotBlank
    private String action;
    private Long bizId;
    private Map<String, Object> input;
}
