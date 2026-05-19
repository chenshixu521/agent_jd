package com.agentjd.service;

import com.agentjd.dto.LoginRequest;
import com.agentjd.dto.RegisterRequest;
import com.agentjd.vo.AuthVO;
import com.agentjd.vo.UserVO;

public interface AuthService {
    AuthVO register(RegisterRequest request);

    AuthVO login(LoginRequest request);

    UserVO me();
}
