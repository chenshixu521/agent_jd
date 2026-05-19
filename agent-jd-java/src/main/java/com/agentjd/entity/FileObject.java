package com.agentjd.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("f_file_object")
public class FileObject {
    @TableId
    private Long id;
    private Long userId;
    private String originalName;
    private String storedName;
    private String contentType;
    private Long sizeBytes;
    private String storagePath;
    private String url;
    private LocalDateTime createdAt;
}
