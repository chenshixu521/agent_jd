package com.agentjd.agent;

import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import com.agentjd.security.UserContextHolder;
import com.agentjd.web.TraceContext;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.Map;
import java.util.concurrent.TimeoutException;

@Slf4j
@Component
@RequiredArgsConstructor
public class AgentClient {
    private final WebClient agentWebClient;
    private final AgentProperties properties;

    public Map<String, Object> call(String capability, String action, String taskUuid, Map<String, Object> payload) {
        Long userId = UserContextHolder.getUserId();
        String traceId = TraceContext.getTraceId();
        AgentRequest<Map<String, Object>> request = new AgentRequest<>(
                taskUuid,
                false,
                payload,
                new AgentRequest.RequestMeta(traceId, userId, System.currentTimeMillis()));
        long start = System.currentTimeMillis();
        try {
            log.info("Calling Python Agent, taskUuid={}, capability={}, action={}, traceId={}", taskUuid, capability,
                    action, traceId);
            AgentResponse<Map<String, Object>> response = agentWebClient.post()
                    .uri("/v1/{capability}/{action}", capability, action)
                    .header("X-Trace-Id", traceId)
                    .header("X-User-Id", String.valueOf(userId))
                    .header("X-Task-Id", taskUuid)
                    .header(HttpHeaders.AUTHORIZATION, "Bearer " + properties.getInternalToken())
                    .bodyValue(request)
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, clientResponse -> clientResponse.bodyToMono(String.class)
                            .map(body -> new AgentRemoteException(clientResponse.statusCode().value(), body,
                                    clientResponse.statusCode().is5xxServerError())))
                    .bodyToMono(new ParameterizedTypeReference<AgentResponse<Map<String, Object>>>() {
                    })
                    .timeout(Duration.ofMillis(properties.getResponseTimeoutMs()))
                    .retryWhen(Retry
                            .backoff(properties.getMaxRetry(), Duration.ofMillis(properties.getRetryBackoffMs()))
                            .filter(this::isRetryable)
                            .doBeforeRetry(signal -> log.warn(
                                    "Retry Python Agent call, taskUuid={}, capability={}, action={}, retry={}, reason={}",
                                    taskUuid,
                                    capability,
                                    action,
                                    signal.totalRetries() + 1,
                                    signal.failure().getMessage())))
                    .block();
            if (response == null) {
                throw new BizException(ErrorCode.AGENT_CALL_FAILED, "AI Agent 无响应");
            }
            if (!response.isOk()) {
                String message = response.getError() != null && response.getError().getMessage() != null
                        ? response.getError().getMessage()
                        : response.getMsg();
                boolean retryable = response.getError() != null
                        && Boolean.TRUE.equals(response.getError().getRetryable());
                throw new AgentRemoteException(
                        response.getCode() == null ? ErrorCode.AGENT_CALL_FAILED.getCode() : response.getCode(),
                        message, retryable);
            }
            log.info(
                    "Python Agent call success, taskUuid={}, capability={}, action={}, latencyMs={}, remoteTraceId={}",
                    taskUuid,
                    capability,
                    action,
                    System.currentTimeMillis() - start,
                    response.getTraceId());
            return response.getData();
        } catch (AgentRemoteException ex) {
            log.error(
                    "Python Agent returned error, taskUuid={}, capability={}, action={}, code={}, retryable={}, latencyMs={}, message={}",
                    taskUuid,
                    capability,
                    action,
                    ex.getCode(),
                    ex.isRetryable(),
                    System.currentTimeMillis() - start,
                    ex.getMessage());
            throw new BizException(ErrorCode.AGENT_CALL_FAILED, ex.getMessage(), ex.isRetryable());
        } catch (WebClientResponseException ex) {
            log.error("Python Agent HTTP error, taskUuid={}, status={}, body={}", taskUuid, ex.getStatusCode(),
                    ex.getResponseBodyAsString(), ex);
            throw new BizException(
                    ErrorCode.AGENT_CALL_FAILED,
                    "AI Agent HTTP 异常: " + ex.getStatusCode(),
                    isRetryable(ex));
        } catch (BizException ex) {
            throw ex;
        } catch (Exception ex) {
            log.error(
                    "Python Agent call failed, taskUuid={}, capability={}, action={}, latencyMs={}",
                    taskUuid,
                    capability,
                    action,
                    System.currentTimeMillis() - start,
                    ex);
            throw new BizException(ErrorCode.AGENT_CALL_FAILED, ex.getMessage(), isRetryable(ex));
        }
    }

    private boolean isRetryable(Throwable throwable) {
        if (throwable instanceof AgentRemoteException ex) {
            return ex.isRetryable();
        }
        if (throwable instanceof WebClientResponseException ex) {
            int status = ex.getStatusCode().value();
            return status == 408 || status == 409 || status == 429 || status >= 500;
        }
        boolean retryable = throwable instanceof TimeoutException
                || throwable instanceof java.io.IOException
                || throwable instanceof java.net.ConnectException;
        if (retryable) {
            return true;
        }
        return throwable.getCause() != null && throwable.getCause() != throwable && isRetryable(throwable.getCause());
    }
}
