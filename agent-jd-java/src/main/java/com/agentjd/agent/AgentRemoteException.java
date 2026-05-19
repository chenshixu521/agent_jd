package com.agentjd.agent;

import lombok.Getter;

@Getter
public class AgentRemoteException extends RuntimeException {
    private final int code;
    private final boolean retryable;

    public AgentRemoteException(int code, String message, boolean retryable) {
        super(message);
        this.code = code;
        this.retryable = retryable;
    }
}
