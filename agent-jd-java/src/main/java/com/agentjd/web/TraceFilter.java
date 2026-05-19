package com.agentjd.web;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class TraceFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        String traceId = request.getHeader("X-Trace-Id");
        TraceContext.setTraceId(traceId);
        MDC.put("traceId", TraceContext.getTraceId());
        response.setHeader("X-Trace-Id", TraceContext.getTraceId());
        try {
            filterChain.doFilter(request, response);
        } finally {
            MDC.remove("traceId");
            TraceContext.clear();
        }
    }
}
