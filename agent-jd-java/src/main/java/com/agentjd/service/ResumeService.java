package com.agentjd.service;

import com.agentjd.dto.ResumeCreateRequest;
import com.agentjd.dto.ResumeUpdateRequest;
import com.agentjd.vo.ResumeVO;

import java.util.List;

public interface ResumeService {
    ResumeVO create(ResumeCreateRequest request);

    List<ResumeVO> list();

    ResumeVO detail(Long id);

    ResumeVO update(Long id, ResumeUpdateRequest request);

    void delete(Long id);
}
