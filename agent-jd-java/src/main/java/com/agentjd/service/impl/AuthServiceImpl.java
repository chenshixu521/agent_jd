package com.agentjd.service.impl;

import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import com.agentjd.security.JwtProperties;
import com.agentjd.security.JwtUtil;
import com.agentjd.security.UserContextHolder;
import com.agentjd.dto.LoginRequest;
import com.agentjd.dto.RegisterRequest;
import com.agentjd.entity.User;
import com.agentjd.mapper.UserMapper;
import com.agentjd.vo.AuthVO;
import com.agentjd.vo.UserVO;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import com.agentjd.service.AuthService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {
    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final JwtProperties jwtProperties;

    @Transactional(rollbackFor = Exception.class)
    @Override
    public AuthVO register(RegisterRequest request) {
        Long count = userMapper.selectCount(new LambdaQueryWrapper<User>().eq(User::getUsername, request.getUsername()));
        if (count > 0) {
            throw new BizException(ErrorCode.DUPLICATE_USERNAME);
        }
        User user = new User();
        user.setUsername(request.getUsername());
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));
        user.setEmail(request.getEmail());
        user.setPhone(request.getPhone());
        user.setStatus(1);
        user.setRole("USER");
        user.setDeleted(0);
        userMapper.insert(user);
        return buildAuth(user);
    }

    @Override
    public AuthVO login(LoginRequest request) {
        User user = userMapper.selectOne(new LambdaQueryWrapper<User>().eq(User::getUsername, request.getUsername()).eq(User::getDeleted, 0));
        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new BizException(ErrorCode.PASSWORD_INVALID);
        }
        if (!Integer.valueOf(1).equals(user.getStatus())) {
            throw new BizException(ErrorCode.FORBIDDEN, "账号已被禁用");
        }
        return buildAuth(user);
    }

    @Override
    public UserVO me() {
        User user = userMapper.selectById(UserContextHolder.getUserId());
        if (user == null) {
            throw new BizException(ErrorCode.AUTH_INVALID);
        }
        return toVO(user);
    }

    private AuthVO buildAuth(User user) {
        return AuthVO.builder()
                .accessToken(jwtUtil.createToken(user.getId(), user.getUsername()))
                .tokenType("Bearer")
                .expiresIn(jwtProperties.getAccessTokenTtlSeconds())
                .user(toVO(user))
                .build();
    }

    private UserVO toVO(User user) {
        return UserVO.builder()
                .id(user.getId())
                .username(user.getUsername())
                .email(user.getEmail())
                .phone(user.getPhone())
                .role(user.getRole())
                .build();
    }
}
