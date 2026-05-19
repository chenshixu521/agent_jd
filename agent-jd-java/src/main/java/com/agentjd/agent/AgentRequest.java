package com.agentjd.agent;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AgentRequest<T> {
    private String taskId;
    private Boolean stream;
    private T payload;
    private RequestMeta meta;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RequestMeta {
        private String traceId;
        private Long userId;
        private Long timestamp;
    }
}
