package com.agentjd.agent;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "agent.python")
public class AgentProperties {
    private String baseUrl;
    private String internalToken;
    private Integer connectTimeoutMs = 3000;
    private Integer responseTimeoutMs = 120000;
    private Integer maxRetry = 2;
    private Integer retryBackoffMs = 300;
}
