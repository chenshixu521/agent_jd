package com.agentjd;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@MapperScan("com.agentjd.mapper")
@EnableScheduling
@SpringBootApplication
public class AgentJdApplication {

    public static void main(String[] args) {
        SpringApplication.run(AgentJdApplication.class, args);
    }
}
