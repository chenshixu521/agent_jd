package com.agentjd.service.impl;

import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import com.agentjd.entity.FileObject;
import com.agentjd.mapper.FileObjectMapper;
import com.agentjd.vo.FileVO;
import com.agentjd.security.UserContextHolder;
import com.agentjd.storage.LocalStorageProperties;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import com.agentjd.service.FileService;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class FileServiceImpl implements FileService {
    private final FileObjectMapper fileObjectMapper;
    private final LocalStorageProperties storageProperties;

    @Override
    public FileVO upload(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new BizException(ErrorCode.PARAM_INVALID, "上传文件不能为空");
        }
        Long userId = UserContextHolder.getUserId();
        String datePath = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMM"));
        String originalName = file.getOriginalFilename() == null ? "unknown" : file.getOriginalFilename();
        String ext = "";
        int dot = originalName.lastIndexOf('.');
        if (dot >= 0) {
            ext = originalName.substring(dot);
        }
        String storedName = UUID.randomUUID() + ext;
        Path dir = Path.of(storageProperties.getRootPath(), String.valueOf(userId), datePath);
        Path target = dir.resolve(storedName);
        try {
            Files.createDirectories(dir);
            file.transferTo(target);
        } catch (IOException ex) {
            throw new BizException(ErrorCode.FILE_UPLOAD_FAILED, ex.getMessage());
        }
        FileObject object = new FileObject();
        object.setUserId(userId);
        object.setOriginalName(originalName);
        object.setStoredName(storedName);
        object.setContentType(file.getContentType());
        object.setSizeBytes(file.getSize());
        object.setStoragePath(target.toAbsolutePath().toString());
        object.setCreatedAt(LocalDateTime.now());
        fileObjectMapper.insert(object);
        object.setUrl(storageProperties.getPublicBaseUrl() + "/" + object.getId());
        fileObjectMapper.updateById(object);
        return toVO(object);
    }

    @Override
    public FileObject requireOwnFile(Long id) {
        FileObject object = fileObjectMapper.selectOne(new LambdaQueryWrapper<FileObject>().eq(FileObject::getId, id).eq(FileObject::getUserId, UserContextHolder.getUserId()));
        if (object == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "文件不存在");
        }
        return object;
    }

    @Override
    public Resource download(Long id) {
        FileObject object = requireOwnFile(id);
        return new FileSystemResource(Path.of(object.getStoragePath()));
    }

    @Override
    public FileVO detail(Long id) {
        return toVO(requireOwnFile(id));
    }

    private FileVO toVO(FileObject object) {
        return FileVO.builder()
                .id(object.getId())
                .originalName(object.getOriginalName())
                .contentType(object.getContentType())
                .sizeBytes(object.getSizeBytes())
                .url(object.getUrl())
                .build();
    }
}
