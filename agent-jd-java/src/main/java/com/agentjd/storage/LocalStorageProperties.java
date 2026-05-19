package com.agentjd.storage;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "storage.local")
public class LocalStorageProperties {
    private String rootPath;
    private String publicBaseUrl;
}
