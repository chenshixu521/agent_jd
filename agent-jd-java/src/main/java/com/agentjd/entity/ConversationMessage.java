package com.agentjd.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("c_conversation_message")
public class ConversationMessage {
    @TableId
    private Long id;
    private Long conversationId;
    private Long userId;
    private String role;
    private String content;
    private String taskUuid;
    private String metadataJson;
    private LocalDateTime createdAt;
}
