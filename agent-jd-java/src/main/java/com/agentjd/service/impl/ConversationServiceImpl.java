package com.agentjd.service.impl;

import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import com.agentjd.dto.ConversationCreateRequest;
import com.agentjd.dto.MessageCreateRequest;
import com.agentjd.entity.Conversation;
import com.agentjd.entity.ConversationMessage;
import com.agentjd.mapper.ConversationMapper;
import com.agentjd.mapper.ConversationMessageMapper;
import com.agentjd.vo.ConversationVO;
import com.agentjd.vo.MessageVO;
import com.agentjd.security.UserContextHolder;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import com.agentjd.service.ConversationService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class ConversationServiceImpl implements ConversationService {
    private final ConversationMapper conversationMapper;
    private final ConversationMessageMapper messageMapper;
    private final ObjectMapper objectMapper;

    @Transactional(rollbackFor = Exception.class)
    @Override
    public ConversationVO create(ConversationCreateRequest request) {
        Conversation conversation = new Conversation();
        conversation.setUserId(UserContextHolder.getUserId());
        conversation.setTitle(request.getTitle());
        conversation.setScene(request.getScene());
        conversation.setCreatedAt(LocalDateTime.now());
        conversation.setUpdatedAt(LocalDateTime.now());
        conversation.setDeleted(0);
        conversationMapper.insert(conversation);
        return toVO(conversation);
    }

    @Override
    public List<ConversationVO> list() {
        return conversationMapper.selectList(new LambdaQueryWrapper<Conversation>()
                        .eq(Conversation::getUserId, UserContextHolder.getUserId())
                        .eq(Conversation::getDeleted, 0)
                        .orderByDesc(Conversation::getUpdatedAt))
                .stream().map(this::toVO).toList();
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public MessageVO addMessage(Long conversationId, MessageCreateRequest request) {
        Conversation conversation = requireOwnConversation(conversationId);
        ConversationMessage message = new ConversationMessage();
        message.setConversationId(conversationId);
        message.setUserId(UserContextHolder.getUserId());
        message.setRole(request.getRole());
        message.setContent(request.getContent());
        message.setTaskUuid(request.getTaskUuid());
        message.setMetadataJson(toJson(request.getMetadata()));
        message.setCreatedAt(LocalDateTime.now());
        messageMapper.insert(message);
        conversation.setUpdatedAt(LocalDateTime.now());
        conversationMapper.updateById(conversation);
        return toVO(message);
    }

    @Override
    public List<MessageVO> messages(Long conversationId) {
        requireOwnConversation(conversationId);
        return messageMapper.selectList(new LambdaQueryWrapper<ConversationMessage>()
                        .eq(ConversationMessage::getConversationId, conversationId)
                        .eq(ConversationMessage::getUserId, UserContextHolder.getUserId())
                        .orderByAsc(ConversationMessage::getCreatedAt))
                .stream().map(this::toVO).toList();
    }

    private Conversation requireOwnConversation(Long id) {
        Conversation conversation = conversationMapper.selectOne(new LambdaQueryWrapper<Conversation>()
                .eq(Conversation::getId, id)
                .eq(Conversation::getUserId, UserContextHolder.getUserId())
                .eq(Conversation::getDeleted, 0));
        if (conversation == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "对话不存在");
        }
        return conversation;
    }

    private ConversationVO toVO(Conversation conversation) {
        return ConversationVO.builder()
                .id(conversation.getId())
                .title(conversation.getTitle())
                .scene(conversation.getScene())
                .createdAt(conversation.getCreatedAt())
                .updatedAt(conversation.getUpdatedAt())
                .build();
    }

    private MessageVO toVO(ConversationMessage message) {
        return MessageVO.builder()
                .id(message.getId())
                .conversationId(message.getConversationId())
                .role(message.getRole())
                .content(message.getContent())
                .taskUuid(message.getTaskUuid())
                .metadata(fromJson(message.getMetadataJson()))
                .createdAt(message.getCreatedAt())
                .build();
    }

    private String toJson(Object value) {
        try {
            return value == null ? null : objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException ex) {
            throw new BizException(ErrorCode.PARAM_INVALID, "metadata 不是合法 JSON");
        }
    }

    private Object fromJson(String json) {
        if (json == null || json.isBlank()) {
            return null;
        }
        try {
            return objectMapper.readValue(json, new TypeReference<Map<String, Object>>() {});
        } catch (JsonProcessingException ex) {
            return json;
        }
    }
}
