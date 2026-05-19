package com.agentjd.vo;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class AuthVO {
    private String accessToken;
    private String tokenType;
    private Long expiresIn;
    private UserVO user;
}
