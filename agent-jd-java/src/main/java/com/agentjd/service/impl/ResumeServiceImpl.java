package com.agentjd.service.impl;

import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import com.agentjd.entity.FileObject;
import com.agentjd.mapper.FileObjectMapper;
import com.agentjd.dto.ResumeCreateRequest;
import com.agentjd.dto.ResumeUpdateRequest;
import com.agentjd.entity.Resume;
import com.agentjd.mapper.ResumeMapper;
import com.agentjd.vo.ResumeVO;
import com.agentjd.security.UserContextHolder;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import lombok.RequiredArgsConstructor;
import com.agentjd.service.DocumentTextExtractorService;
import com.agentjd.service.ResumeService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ResumeServiceImpl implements ResumeService {
    private final ResumeMapper resumeMapper;
    private final FileObjectMapper fileObjectMapper;
    private final DocumentTextExtractorService documentTextExtractorService;

    @Transactional(rollbackFor = Exception.class)
    @Override
    public ResumeVO create(ResumeCreateRequest request) {
        Long userId = UserContextHolder.getUserId();
        Resume resume = new Resume();
        resume.setUserId(userId);
        resume.setTitle(request.getTitle());
        resume.setSource(request.getFileId() == null ? 2 : 1);
        resume.setFileId(request.getFileId());
        String rawText = request.getRawText();
        resume.setStatus(1);
        resume.setDeleted(0);
        resume.setCreatedAt(LocalDateTime.now());
        resume.setUpdatedAt(LocalDateTime.now());
        if (request.getFileId() != null) {
            FileObject file = fileObjectMapper.selectById(request.getFileId());
            if (file == null || !userId.equals(file.getUserId())) {
                throw new BizException(ErrorCode.NOT_FOUND, "文件不存在");
            }
            resume.setFileUrl(file.getUrl());
            if (rawText == null || rawText.isBlank()) {
                rawText = documentTextExtractorService.extract(Path.of(file.getStoragePath()), file.getOriginalName(),
                        file.getContentType());
            }
        }
        if (rawText == null || rawText.isBlank()) {
            throw new BizException(ErrorCode.PARAM_INVALID, "请上传简历文件或填写简历文本");
        }
        resume.setRawText(rawText);
        resumeMapper.insert(resume);
        return toVO(resume);
    }

    @Override
    public List<ResumeVO> list() {
        return resumeMapper.selectList(new LambdaQueryWrapper<Resume>()
                .eq(Resume::getUserId, UserContextHolder.getUserId())
                .eq(Resume::getDeleted, 0)
                .orderByDesc(Resume::getCreatedAt))
                .stream().map(this::toVO).toList();
    }

    @Override
    public ResumeVO detail(Long id) {
        return toVO(requireOwnResume(id));
    }

    private Resume requireOwnResume(Long id) {
        Resume resume = resumeMapper.selectOne(new LambdaQueryWrapper<Resume>()
                .eq(Resume::getId, id)
                .eq(Resume::getUserId, UserContextHolder.getUserId())
                .eq(Resume::getDeleted, 0));
        if (resume == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "简历不存在");
        }
        return resume;
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public ResumeVO update(Long id, ResumeUpdateRequest request) {
        Resume resume = requireOwnResume(id);
        resume.setTitle(request.getTitle());
        resume.setRawText(request.getRawText());
        if (request.getStatus() != null) {
            resume.setStatus(request.getStatus());
        }
        resume.setUpdatedAt(LocalDateTime.now());
        resumeMapper.updateById(resume);
        return toVO(resume);
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public void delete(Long id) {
        Long userId = UserContextHolder.getUserId();
        int updated = resumeMapper.update(null, new LambdaUpdateWrapper<Resume>()
                .eq(Resume::getId, id)
                .eq(Resume::getUserId, userId)
                .eq(Resume::getDeleted, 0)
                .set(Resume::getDeleted, 1)
                .set(Resume::getUpdatedAt, LocalDateTime.now()));
        if (updated == 0) {
            throw new BizException(ErrorCode.NOT_FOUND, "简历不存在");
        }
    }

    private ResumeVO toVO(Resume resume) {
        return ResumeVO.builder()
                .id(resume.getId())
                .title(resume.getTitle())
                .source(resume.getSource())
                .fileId(resume.getFileId())
                .fileUrl(resume.getFileUrl())
                .rawText(resume.getRawText())
                .status(resume.getStatus())
                .createdAt(resume.getCreatedAt())
                .updatedAt(resume.getUpdatedAt())
                .build();
    }
}
