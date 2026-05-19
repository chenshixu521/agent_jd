package com.agentjd.security;

import com.agentjd.common.ApiResponse;
import com.agentjd.common.ErrorCode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.slf4j.MDC;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;

@Component
@RequiredArgsConstructor
public class JwtAuthFilter extends OncePerRequestFilter {
    private final JwtUtil jwtUtil;
    private final ObjectMapper objectMapper;

    private static final List<String> WHITE_LIST = List.of(
            "/api/auth/register",
            "/api/auth/login",
            "/actuator",
            "/error"
    );

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return WHITE_LIST.stream().anyMatch(path::startsWith);
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        String authorization = request.getHeader("Authorization");
        if (authorization == null || !authorization.startsWith("Bearer ")) {
            writeUnauthorized(response, ErrorCode.AUTH_REQUIRED);
            return;
        }
        try {
            JwtUser jwtUser = jwtUtil.parseToken(authorization.substring(7));
            UserContextHolder.set(new UserContext(jwtUser.userId(), jwtUser.username()));
            MDC.put("userId", String.valueOf(jwtUser.userId()));
            filterChain.doFilter(request, response);
        } catch (Exception ex) {
            writeUnauthorized(response, ErrorCode.AUTH_INVALID);
        } finally {
            MDC.remove("userId");
            UserContextHolder.clear();
        }
    }

    private void writeUnauthorized(HttpServletResponse response, ErrorCode errorCode) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.getWriter().write(objectMapper.writeValueAsString(ApiResponse.fail(errorCode)));
    }
}
