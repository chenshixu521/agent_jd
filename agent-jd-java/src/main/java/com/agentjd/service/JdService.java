package com.agentjd.service;

import com.agentjd.dto.JdCreateRequest;
import com.agentjd.dto.JdUpdateRequest;
import com.agentjd.vo.JdVO;

import java.util.List;

public interface JdService {
    JdVO create(JdCreateRequest request);

    List<JdVO> list();

    JdVO detail(Long id);

    JdVO update(Long id, JdUpdateRequest request);

    void delete(Long id);
}
