package com.agentjd.service;

import com.agentjd.dto.ConversationCreateRequest;
import com.agentjd.dto.MessageCreateRequest;
import com.agentjd.vo.ConversationVO;
import com.agentjd.vo.MessageVO;

import java.util.List;

public interface ConversationService {
    ConversationVO create(ConversationCreateRequest request);

    List<ConversationVO> list();

    MessageVO addMessage(Long conversationId, MessageCreateRequest request);

    List<MessageVO> messages(Long conversationId);
}
