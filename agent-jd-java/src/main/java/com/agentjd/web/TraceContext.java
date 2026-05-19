package com.agentjd.web;

import java.util.UUID;

public final class TraceContext {
    private static final ThreadLocal<String> HOLDER = new ThreadLocal<>();

    private TraceContext() {
    }

    public static void setTraceId(String traceId) {
        HOLDER.set(traceId == null || traceId.isBlank() ? UUID.randomUUID().toString() : traceId);
    }

    public static String getTraceId() {
        String traceId = HOLDER.get();
        if (traceId == null) {
            traceId = UUID.randomUUID().toString();
            HOLDER.set(traceId);
        }
        return traceId;
    }

    public static void clear() {
        HOLDER.remove();
    }
}
