package com.agentjd.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ResumeUpdateRequest {
    @NotBlank
    private String title;
    private String rawText;
    private Integer status;
}
