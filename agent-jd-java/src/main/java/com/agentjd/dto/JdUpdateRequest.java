package com.agentjd.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class JdUpdateRequest {
    @NotBlank
    private String title;
    private String company;
    private String city;
    @NotBlank
    private String rawText;
    private String sourceUrl;
    private Integer status;
}
