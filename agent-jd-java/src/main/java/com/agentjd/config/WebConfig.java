package com.agentjd.config;

import com.agentjd.security.JwtAuthFilter;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@RequiredArgsConstructor
@EnableConfigurationProperties({com.agentjd.security.JwtProperties.class, com.agentjd.storage.LocalStorageProperties.class, com.agentjd.agent.AgentProperties.class})
public class WebConfig implements WebMvcConfigurer {
    private final JwtAuthFilter jwtAuthFilter;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
    }
}
