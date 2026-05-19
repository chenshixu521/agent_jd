package com.agentjd.controller;

import com.agentjd.dto.AiTaskSubmitRequest;
import com.agentjd.service.AiTaskService;
import com.agentjd.vo.AiTaskVO;
import com.agentjd.common.ApiResponse;
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
@RequestMapping("/api/tasks")
public class AiTaskController {
    private final AiTaskService aiTaskService;

    @PostMapping
    public ApiResponse<AiTaskVO> submit(@Valid @RequestBody AiTaskSubmitRequest request) {
        return ApiResponse.ok(aiTaskService.submit(request));
    }

    @GetMapping
    public ApiResponse<List<AiTaskVO>> list() {
        return ApiResponse.ok(aiTaskService.list());
    }

    @GetMapping("/{taskUuid}")
    public ApiResponse<AiTaskVO> detail(@PathVariable String taskUuid) {
        return ApiResponse.ok(aiTaskService.detail(taskUuid));
    }

    @GetMapping("/{taskUuid}/result")
    public ApiResponse<AiTaskVO> result(@PathVariable String taskUuid) {
        return ApiResponse.ok(aiTaskService.result(taskUuid));
    }
}
