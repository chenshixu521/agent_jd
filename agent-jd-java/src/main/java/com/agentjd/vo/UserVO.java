package com.agentjd.vo;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class UserVO {
    private Long id;
    private String username;
    private String email;
    private String phone;
    private String role;
}
