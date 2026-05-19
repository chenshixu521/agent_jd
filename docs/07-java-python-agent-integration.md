# 07 - Spring Boot 调用 Python Agent 服务完整方案

本文档说明 Java 后端通过 `WebClient` 调用 Python FastAPI Agent 服务的企业级通信方案。

---

## 1. 通信拓扑

```text
Vue3 Frontend
    │
    ▼
Spring Boot Java Backend
    │  WebClient + JSON + Bearer Internal Token
    ▼
Python FastAPI Agent Service
    │
    ├── LangGraph 工作流
    ├── Tool 调用
    ├── Redis 上下文/任务状态
    └── FAISS/RAG 检索
```

---

## 2. Java 调用封装

核心类：

| 类 | 责任 |
| --- | --- |
| `AgentClient` | WebClient 调用 Python Agent，处理超时、重试、日志、异常映射 |
| `AgentRequest<T>` | Java → Python 请求结构，包含 `taskId/stream/payload/meta` |
| `AgentResponse<T>` | Python → Java 响应结构，包含 `code/msg/success/taskId/data/error/traceId` |
| `AgentErrorPayload` | Python 结构化错误载荷 |
| `AgentRemoteException` | Java 内部封装远端错误，标记是否可重试 |
| `AiTaskService` | AI 任务状态管理，负责 PENDING/RUNNING/SUCCESS/FAILED 落库与 Redis 缓存 |

---

## 3. Python API 设计

统一路径：

```http
POST /v1/{capability}/{action}
```

已支持：

| capability | action | 说明 |
| --- | --- | --- |
| `resume` | `parse` / `optimize` / `advice` | 简历解析、优化建议 |
| `jd` | `analyze` / `parse` | JD 解析 |
| `keyword` | `extract` | 技能关键词提取 |
| `project` | `rewrite` | 项目改写 |
| `greeting` | `generate` | 打招呼生成 |
| `match` | `analyze` | 岗位匹配分析 |
| `chat` | `message` / `talk` | 多轮对话 |

---

## 4. DTO 设计

### 4.1 请求 DTO

```json
{
  "taskId": "9a9e3f8e-xxxx-xxxx-xxxx",
  "stream": false,
  "payload": {
    "resume_text": "...",
    "jd_text": "..."
  },
  "meta": {
    "traceId": "trace-id",
    "userId": 1001,
    "timestamp": 1710000000000
  }
}
```

### 4.2 响应 DTO

```json
{
  "code": 0,
  "msg": "ok",
  "success": true,
  "taskId": "9a9e3f8e-xxxx-xxxx-xxxx",
  "data": {
    "jd": {},
    "keywords": {},
    "events": []
  },
  "error": null,
  "traceId": "trace-id"
}
```

### 4.3 失败响应

```json
{
  "code": 50001,
  "msg": "LLM 调用失败",
  "success": false,
  "taskId": "9a9e3f8e-xxxx-xxxx-xxxx",
  "data": null,
  "error": {
    "type": "AgentError",
    "message": "LLM 调用失败",
    "retryable": true
  },
  "traceId": "trace-id"
}
```

---

## 5. 超时处理

Java 侧配置：

```yaml
agent:
  python:
    connect-timeout-ms: 3000
    response-timeout-ms: 120000
```

实现位置：

- Netty `CONNECT_TIMEOUT_MILLIS`
- Netty `responseTimeout`
- Reactor `Mono.timeout(Duration.ofMillis(responseTimeoutMs))`

---

## 6. 重试机制

Java 侧配置：

```yaml
agent:
  python:
    max-retry: 2
    retry-backoff-ms: 300
```

仅重试：

- 连接异常
- 读写超时
- HTTP 502/503/504
- Python 返回 `error.retryable=true`

不重试：

- 参数错误
- 鉴权失败
- capability/action 不存在
- 业务不可恢复错误

---

## 7. 日志追踪

请求头：

```http
X-Trace-Id: trace-id
X-User-Id: 1001
X-Task-Id: task-uuid
Authorization: Bearer internal-token
```

Java 日志：

```text
Calling Python Agent, taskUuid=..., capability=..., action=..., traceId=...
Python Agent call success, taskUuid=..., latencyMs=..., remoteTraceId=...
Retry Python Agent call, retry=1, reason=...
Python Agent returned error, code=..., retryable=...
```

Python 日志：

```text
Agent request start taskId=... capability=... action=... traceId=...
Agent request success taskId=... capability=... action=... traceId=...
Agent request failed taskId=... capability=... action=... traceId=...
```

---

## 8. 异常处理

Java：

- `AgentRemoteException` 表示 Python 结构化错误或 HTTP 错误
- `BizException(ErrorCode.AGENT_CALL_FAILED)` 对 Controller 统一返回
- `GlobalExceptionHandler` 输出统一 `ApiResponse`

Python：

- `AgentError` 输出 `success=false + error`
- 未捕获异常输出 `SYSTEM_ERROR + retryable=true`
- HTTP 状态保持 200，业务状态由 `code/success/error` 表达，便于 Java 统一解析

---

## 9. AI 任务状态管理

Java MySQL 状态：

| 状态 | code | 含义 |
| --- | --- | --- |
| `PENDING` | 0 | 已创建，等待调用 |
| `RUNNING` | 1 | 调用 Python 中 |
| `SUCCESS` | 2 | Python 返回成功 |
| `FAILED` | 3 | 调用失败或 Agent 执行失败 |
| `CANCELED` | 4 | 取消 |

Java Redis：

```text
ai:task:{taskUuid} -> AiTaskVO，TTL 24h
```

Python Redis：

```text
agent:task:{taskId}    -> Python 执行状态，TTL 24h
agent:context:{taskId} -> 请求与结果上下文，TTL 24h
agent:event:{taskId}   -> LangGraph 节点事件，TTL 24h
```

---

## 10. 可运行验证

### 启动 Python

```bash
cd agent-jd-python
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 启动 Java

```bash
cd agent-jd-java
mvn spring-boot:run
```

### Java 调用入口

```http
POST /api/tasks
Authorization: Bearer {jwt}
Content-Type: application/json

{
  "capability": "jd",
  "action": "analyze",
  "bizId": 1,
  "input": {
    "jd_text": "招聘 Java 后端工程师，要求 Spring Boot、MySQL、Redis。"
  }
}
```
