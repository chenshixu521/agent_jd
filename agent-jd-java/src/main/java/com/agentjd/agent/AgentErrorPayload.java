package com.agentjd.agent;

import lombok.Data;

@Data
public class AgentErrorPayload {
    private String type;
    private String message;
    private Boolean retryable;
}
