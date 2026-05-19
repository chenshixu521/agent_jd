package com.agentjd.controller;

import com.agentjd.common.ApiResponse;
import com.agentjd.dto.ConversationCreateRequest;
import com.agentjd.dto.MessageCreateRequest;
import com.agentjd.service.ConversationService;
import com.agentjd.vo.ConversationVO;
import com.agentjd.vo.MessageVO;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/conversations")
public class ConversationController {
    private final ConversationService conversationService;

    @PostMapping
    public ApiResponse<ConversationVO> create(@Valid @RequestBody ConversationCreateRequest request) {
        return ApiResponse.ok(conversationService.create(request));
    }

    @GetMapping
    public ApiResponse<List<ConversationVO>> list() {
        return ApiResponse.ok(conversationService.list());
    }

    @PostMapping("/{conversationId}/messages")
    public ApiResponse<MessageVO> addMessage(@PathVariable Long conversationId, @Valid @RequestBody MessageCreateRequest request) {
        return ApiResponse.ok(conversationService.addMessage(conversationId, request));
    }

    @GetMapping("/{conversationId}/messages")
    public ApiResponse<List<MessageVO>> messages(@PathVariable Long conversationId) {
        return ApiResponse.ok(conversationService.messages(conversationId));
    }
}
