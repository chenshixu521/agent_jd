package com.agentjd.entity;

import lombok.Getter;

@Getter
public enum AiTaskStatus {
    PENDING(0),
    RUNNING(1),
    SUCCESS(2),
    FAILED(3),
    CANCELED(4);

    private final int code;

    AiTaskStatus(int code) {
        this.code = code;
    }
}
