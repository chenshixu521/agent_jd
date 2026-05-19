package com.agentjd.web;

import com.agentjd.common.ApiResponse;
import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import jakarta.validation.ConstraintViolationException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.BindException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BizException.class)
    public ApiResponse<Void> handleBizException(BizException ex) {
        return ApiResponse.fail(ex.getErrorCode().getCode(), ex.getMessage());
    }

    @ExceptionHandler({MethodArgumentNotValidException.class, BindException.class, ConstraintViolationException.class, HttpMessageNotReadableException.class})
    public ApiResponse<Void> handleParamException(Exception ex) {
        return ApiResponse.fail(ErrorCode.PARAM_INVALID.getCode(), ex.getMessage());
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ApiResponse<Void> handleUploadSize(MaxUploadSizeExceededException ex) {
        return ApiResponse.fail(ErrorCode.FILE_UPLOAD_FAILED.getCode(), "文件大小超过限制");
    }

    @ExceptionHandler(Exception.class)
    public ApiResponse<Void> handleException(Exception ex) {
        log.error("Unhandled exception", ex);
        return ApiResponse.fail(ErrorCode.SYSTEM_ERROR);
    }
}
