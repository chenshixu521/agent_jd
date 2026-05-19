package com.agentjd.controller;

import com.agentjd.common.ApiResponse;
import com.agentjd.entity.FileObject;
import com.agentjd.service.FileService;
import com.agentjd.vo.FileVO;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.nio.charset.StandardCharsets;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/files")
public class FileController {
    private final FileService fileService;

    @PostMapping("/upload")
    public ApiResponse<FileVO> upload(@RequestParam("file") MultipartFile file) {
        return ApiResponse.ok(fileService.upload(file));
    }

    @GetMapping("/{id}")
    public ApiResponse<FileVO> detail(@PathVariable Long id) {
        return ApiResponse.ok(fileService.detail(id));
    }

    @GetMapping("/download/{id}")
    public ResponseEntity<Resource> download(@PathVariable Long id) {
        FileObject object = fileService.requireOwnFile(id);
        Resource resource = fileService.download(id);
        String filename = java.net.URLEncoder.encode(object.getOriginalName(), StandardCharsets.UTF_8).replace("+",
                "%20");
        return ResponseEntity.ok()
                .contentType(MediaType
                        .parseMediaType(object.getContentType() == null ? MediaType.APPLICATION_OCTET_STREAM_VALUE
                                : object.getContentType()))
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename*=UTF-8''" + filename)
                .body(resource);
    }
}
