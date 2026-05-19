package com.agentjd.common;

import lombok.Getter;

@Getter
public enum ErrorCode {
    OK(0, "ok"),
    PARAM_INVALID(40001, "参数错误"),
    AUTH_REQUIRED(40101, "未登录"),
    AUTH_INVALID(40102, "登录已失效"),
    FORBIDDEN(40301, "无权限访问"),
    NOT_FOUND(40401, "资源不存在"),
    DUPLICATE_USERNAME(40901, "用户名已存在"),
    PASSWORD_INVALID(40103, "用户名或密码错误"),
    FILE_UPLOAD_FAILED(50010, "文件上传失败"),
    AGENT_CALL_FAILED(50301, "AI Agent 服务调用失败"),
    SYSTEM_ERROR(50000, "系统异常");

    private final Integer code;
    private final String message;

    ErrorCode(Integer code, String message) {
        this.code = code;
        this.message = message;
    }
}
