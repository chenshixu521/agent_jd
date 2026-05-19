package com.agentjd.vo;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class JdVO {
    private Long id;
    private String title;
    private String company;
    private String city;
    private String rawText;
    private String sourceUrl;
    private Integer status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
