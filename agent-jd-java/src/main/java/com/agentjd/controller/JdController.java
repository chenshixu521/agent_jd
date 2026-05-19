package com.agentjd.controller;

import com.agentjd.common.ApiResponse;
import com.agentjd.dto.JdCreateRequest;
import com.agentjd.dto.JdUpdateRequest;
import com.agentjd.service.JdService;
import com.agentjd.vo.JdVO;
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
@RequestMapping("/api/jds")
public class JdController {
    private final JdService jdService;

    @PostMapping
    public ApiResponse<JdVO> create(@Valid @RequestBody JdCreateRequest request) {
        return ApiResponse.ok(jdService.create(request));
    }

    @GetMapping
    public ApiResponse<List<JdVO>> list() {
        return ApiResponse.ok(jdService.list());
    }

    @GetMapping("/{id}")
    public ApiResponse<JdVO> detail(@PathVariable Long id) {
        return ApiResponse.ok(jdService.detail(id));
    }

    @PutMapping("/{id}")
    public ApiResponse<JdVO> update(@PathVariable Long id, @Valid @RequestBody JdUpdateRequest request) {
        return ApiResponse.ok(jdService.update(id, request));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        jdService.delete(id);
        return ApiResponse.ok();
    }
}
