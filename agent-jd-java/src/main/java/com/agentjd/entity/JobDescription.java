package com.agentjd.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("j_jd")
public class JobDescription {
    @TableId
    private Long id;
    private Long userId;
    private String title;
    private String company;
    private String city;
    private String rawText;
    private String sourceUrl;
    private Integer status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private Integer deleted;
}
