package com.agentjd.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("r_resume")
public class Resume {
    @TableId
    private Long id;
    private Long userId;
    private String title;
    private Integer source;
    private Long fileId;
    private String fileUrl;
    private String rawText;
    private Integer status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private Integer deleted;
}
