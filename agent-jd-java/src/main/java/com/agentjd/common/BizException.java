package com.agentjd.common;

import lombok.Getter;

@Getter
public class BizException extends RuntimeException {
    private final ErrorCode errorCode;
    private final boolean retryable;

    public BizException(ErrorCode errorCode) {
        this(errorCode, errorCode.getMessage(), false);
    }

    public BizException(ErrorCode errorCode, String message) {
        this(errorCode, message, false);
    }

    public BizException(ErrorCode errorCode, String message, boolean retryable) {
        super(message);
        this.errorCode = errorCode;
        this.retryable = retryable;
    }
}
