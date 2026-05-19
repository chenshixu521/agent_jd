package com.agentjd.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ResumeCreateRequest {
    @NotBlank
    private String title;
    private Long fileId;
    private String rawText;
}
