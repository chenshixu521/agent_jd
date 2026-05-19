package com.agentjd.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class RegisterRequest {
    @NotBlank(message = "用户名不为空")
    @Size(min = 3, max = 64)
    private String username;
    @NotBlank(message = "密码不为空")
    @Size(min = 6, max = 64)
    private String password;
    @NotBlank(message = "邮箱不为空")
    private String email;
    private String phone;
}
