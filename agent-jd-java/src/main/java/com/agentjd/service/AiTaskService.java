package com.agentjd.service;

import com.agentjd.dto.AiTaskSubmitRequest;
import com.agentjd.vo.AiTaskVO;

import java.util.List;

public interface AiTaskService {
    AiTaskVO submit(AiTaskSubmitRequest request);

    List<AiTaskVO> list();

    AiTaskVO detail(String taskUuid);

    AiTaskVO result(String taskUuid);
}
