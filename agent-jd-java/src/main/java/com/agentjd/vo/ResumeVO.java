package com.agentjd.vo;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class ResumeVO {
    private Long id;
    private String title;
    private Integer source;
    private Long fileId;
    private String fileUrl;
    private String rawText;
    private Integer status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
