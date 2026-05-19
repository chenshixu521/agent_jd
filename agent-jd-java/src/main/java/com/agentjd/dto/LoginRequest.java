package com.agentjd.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class LoginRequest {
    @NotBlank(message = "用户名不为空")
    private String username;
    @NotBlank(message = "密码不为空")
    private String password;
}
