package com.agentjd.security;

import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;

public final class UserContextHolder {
    private static final ThreadLocal<UserContext> HOLDER = new ThreadLocal<>();

    private UserContextHolder() {
    }

    public static void set(UserContext context) {
        HOLDER.set(context);
    }

    public static UserContext get() {
        UserContext context = HOLDER.get();
        if (context == null) {
            throw new BizException(ErrorCode.AUTH_REQUIRED);
        }
        return context;
    }

    public static Long getUserId() {
        return get().userId();
    }

    public static void clear() {
        HOLDER.remove();
    }
}
