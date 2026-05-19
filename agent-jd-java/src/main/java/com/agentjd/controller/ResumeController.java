package com.agentjd.controller;

import com.agentjd.common.ApiResponse;
import com.agentjd.dto.ResumeCreateRequest;
import com.agentjd.dto.ResumeUpdateRequest;
import com.agentjd.service.ResumeService;
import com.agentjd.vo.ResumeVO;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/resumes")
public class ResumeController {
    private final ResumeService resumeService;

    @PostMapping
    public ApiResponse<ResumeVO> create(@Valid @RequestBody ResumeCreateRequest request) {
        return ApiResponse.ok(resumeService.create(request));
    }

    @GetMapping
    public ApiResponse<List<ResumeVO>> list() {
        return ApiResponse.ok(resumeService.list());
    }

    @GetMapping("/{id}")
    public ApiResponse<ResumeVO> detail(@PathVariable Long id) {
        return ApiResponse.ok(resumeService.detail(id));
    }

    @PutMapping("/{id}")
    public ApiResponse<ResumeVO> update(@PathVariable Long id, @Valid @RequestBody ResumeUpdateRequest request) {
        return ApiResponse.ok(resumeService.update(id, request));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        resumeService.delete(id);
        return ApiResponse.ok();
    }
}
