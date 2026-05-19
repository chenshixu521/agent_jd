package com.agentjd.agent;

import lombok.Data;

@Data
public class AgentResponse<T> {
    private Integer code;
    private String msg;
    private Boolean success;
    private String taskId;
    private T data;
    private AgentErrorPayload error;
    private String traceId;

    public boolean isOk() {
        return (code == null || code == 0) && (success == null || success);
    }
}
