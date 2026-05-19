package com.agentjd.security;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class JwtUtilTest {

    @Test
    void shouldCreateAndParseToken() {
        JwtProperties properties = new JwtProperties();
        properties.setSecret("agent-jd-test-secret-must-be-at-least-32-bytes");
        properties.setAccessTokenTtlSeconds(3600L);
        JwtUtil jwtUtil = new JwtUtil(properties);

        String token = jwtUtil.createToken(1001L, "alice");
        JwtUser jwtUser = jwtUtil.parseToken(token);

        assertThat(jwtUser.userId()).isEqualTo(1001L);
        assertThat(jwtUser.username()).isEqualTo("alice");
    }
}
