package com.agentjd.service.impl;

import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import com.agentjd.dto.JdCreateRequest;
import com.agentjd.dto.JdUpdateRequest;
import com.agentjd.entity.JobDescription;
import com.agentjd.mapper.JobDescriptionMapper;
import com.agentjd.vo.JdVO;
import com.agentjd.security.UserContextHolder;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import com.agentjd.service.JdService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class JdServiceImpl implements JdService {
    private final JobDescriptionMapper jdMapper;

    @Transactional(rollbackFor = Exception.class)
    @Override
    public JdVO create(JdCreateRequest request) {
        JobDescription jd = new JobDescription();
        jd.setUserId(UserContextHolder.getUserId());
        jd.setTitle(request.getTitle());
        jd.setCompany(request.getCompany());
        jd.setCity(request.getCity());
        jd.setRawText(request.getRawText());
        jd.setSourceUrl(request.getSourceUrl());
        jd.setStatus(1);
        jd.setDeleted(0);
        jd.setCreatedAt(LocalDateTime.now());
        jd.setUpdatedAt(LocalDateTime.now());
        jdMapper.insert(jd);
        return toVO(jd);
    }

    @Override
    public List<JdVO> list() {
        return jdMapper.selectList(new LambdaQueryWrapper<JobDescription>()
                .eq(JobDescription::getUserId, UserContextHolder.getUserId())
                .eq(JobDescription::getDeleted, 0)
                .orderByDesc(JobDescription::getCreatedAt))
                .stream().map(this::toVO).toList();
    }

    @Override
    public JdVO detail(Long id) {
        return toVO(requireOwnJd(id));
    }

    private JobDescription requireOwnJd(Long id) {
        JobDescription jd = jdMapper.selectOne(new LambdaQueryWrapper<JobDescription>()
                .eq(JobDescription::getId, id)
                .eq(JobDescription::getUserId, UserContextHolder.getUserId())
                .eq(JobDescription::getDeleted, 0));
        if (jd == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "岗位 JD 不存在");
        }
        return jd;
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public JdVO update(Long id, JdUpdateRequest request) {
        JobDescription jd = requireOwnJd(id);
        jd.setTitle(request.getTitle());
        jd.setCompany(request.getCompany());
        jd.setCity(request.getCity());
        jd.setRawText(request.getRawText());
        jd.setSourceUrl(request.getSourceUrl());
        if (request.getStatus() != null) {
            jd.setStatus(request.getStatus());
        }
        jd.setUpdatedAt(LocalDateTime.now());
        jdMapper.updateById(jd);
        return toVO(jd);
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public void delete(Long id) {
        JobDescription jd = requireOwnJd(id);
        jd.setDeleted(1);
        jd.setUpdatedAt(LocalDateTime.now());
        jdMapper.updateById(jd);
    }

    private JdVO toVO(JobDescription jd) {
        return JdVO.builder()
                .id(jd.getId())
                .title(jd.getTitle())
                .company(jd.getCompany())
                .city(jd.getCity())
                .rawText(jd.getRawText())
                .sourceUrl(jd.getSourceUrl())
                .status(jd.getStatus())
                .createdAt(jd.getCreatedAt())
                .updatedAt(jd.getUpdatedAt())
                .build();
    }
}
