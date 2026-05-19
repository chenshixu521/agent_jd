# 01 - 系统整体架构

本文档对应需求中的 **1. 系统整体架构 / 4. 微服务调用流程 / 7. 数据流**。

---

## 1. 顶层架构图

```
                         ┌──────────────────────────────────────────┐
                         │              用户 (Web 浏览器)             │
                         └────────────────────┬─────────────────────┘
                                              │ HTTPS
                                              ▼
                         ┌──────────────────────────────────────────┐
                         │     Nginx (反向代理 + 静态资源 + 限流)      │
                         └────────────────────┬─────────────────────┘
                                              │
                ┌─────────────────────────────┼──────────────────────────────┐
                │                             │                              │
                ▼                             ▼                              ▼
   ┌────────────────────────┐    ┌────────────────────────┐     ┌────────────────────────┐
   │   Vue3 前端 (SPA)       │    │  Java 主业务后端         │◄───►│  Python Agent 服务      │
   │   Element Plus / Pinia │    │  Spring Boot 3 + MP    │     │  FastAPI + LangGraph   │
   │   Axios                │    │  端口: 8080            │     │  端口: 8000            │
   └────────────────────────┘    └──────────┬─────────────┘     └──────────┬─────────────┘
                                              │                              │
                              ┌───────────────┼─────────────┐    ┌───────────┼───────────┐
                              ▼               ▼             ▼    ▼           ▼           ▼
                       ┌──────────┐   ┌────────────┐  ┌────────────┐  ┌──────────┐ ┌──────────┐
                       │  MySQL   │   │   Redis    │  │  对象存储    │  │  FAISS   │ │  LLM API │
                       │  业务数据  │   │ Cache/队列  │  │ MinIO/OSS  │  │ 向量索引  │ │ OpenAI / │
                       │          │   │            │  │ (简历附件)   │  │          │ │ DashScope│
                       └──────────┘   └────────────┘  └────────────┘  └──────────┘ └──────────┘
```

### 服务边界

| 服务 | 职责 | 端口 | 部署形态 |
| --- | --- | --- | --- |
| `agent-jd-web` | 前端 SPA | 80 (经 Nginx) | 静态文件 |
| `agent-jd-java` | 业务编排、用户/权限/数据持久化 | 8080 | JVM 容器 |
| `agent-jd-python` | AI 推理、Agent 工作流、RAG | 8000 | Python 容器 |
| MySQL | 业务数据 | 3306 | 容器 / RDS |
| Redis | 缓存、任务队列、限流 | 6379 | 容器 / 云 Redis |
| MinIO | 简历/PDF 文件 | 9000 | 容器 / OSS |
| FAISS | 向量索引 | 进程内 (Python) | 持久化目录挂载 |

---

## 2. 分层架构

### 2.1 Java 主业务后端分层 (DDD-Lite)

```
┌─────────────────────────────────────────────────┐
│ interfaces  (controller, dto)                   │  HTTP 入口
├─────────────────────────────────────────────────┤
│ application (service, command, assembler)      │  用例编排
├─────────────────────────────────────────────────┤
│ domain      (entity, repository接口, domain svc)│  领域模型
├─────────────────────────────────────────────────┤
│ infrastructure                                  │
│   ├─ persistence (mapper, po)                  │  MyBatis-Plus
│   ├─ cache       (redis)                       │
│   ├─ remote      (agent client)                │  调用 Python
│   ├─ storage     (minio/oss)                   │
│   └─ mq          (rocketmq/redis stream)       │
└─────────────────────────────────────────────────┘
```

### 2.2 Python Agent 服务分层

```
┌─────────────────────────────────────────────────┐
│ api        (FastAPI router, schema)             │
├─────────────────────────────────────────────────┤
│ agents     (LangGraph 工作流图定义)               │
├─────────────────────────────────────────────────┤
│ chains     (可复用的 LCEL 链)                    │
├─────────────────────────────────────────────────┤
│ tools      (Function Tool: 检索、解析、评分)      │
├─────────────────────────────────────────────────┤
│ rag        (loader, splitter, retriever, store) │
├─────────────────────────────────────────────────┤
│ prompts    (YAML/Jinja2 模板,版本管理)           │
├─────────────────────────────────────────────────┤
│ llm        (LLM/Embedding 抽象 + 多供应商适配)    │
├─────────────────────────────────────────────────┤
│ core       (settings, logger, tracing, error)   │
└─────────────────────────────────────────────────┘
```

---

## 3. 微服务调用流程

### 3.1 同步短任务 (例如 JD 分析)

```
浏览器 ──► Nginx ──► Java /api/jd/analyze
                          │
                          │ 1. JWT 鉴权 + 参数校验
                          │ 2. 落库: jd_record (status=PROCESSING)
                          │ 3. WebClient POST http://agent:8000/v1/jd/analyze
                          ▼
                    Python /v1/jd/analyze
                          │ 1. LangGraph 启动 jd_analyze_graph
                          │ 2. LLM 抽取技能 / 软技能 / 加分项
                          │ 3. 返回结构化 JSON
                          ▼
                    Java 接收 ──► 落库 jd_analysis
                          │
                          ▼
                    返回前端
```

### 3.2 异步长任务 (例如简历优化、项目改写)

```
浏览器 ──► Java POST /api/resume/optimize
              │
              │ 1. 生成 task_id (UUID)
              │ 2. 写 ai_task (status=PENDING) 入库
              │ 3. 推送 Redis Stream: ai:task:queue
              │ 4. 立即返回 task_id
              ▼
       前端拿 task_id
              │
              ├──► (A) 轮询 GET /api/task/{id}
              └──► (B) 订阅 SSE  /api/task/{id}/stream

       Java Worker (监听 Redis Stream)
              │
              │ 1. 取出 task → 调 Python /v1/resume/optimize (流式)
              │ 2. 把 token 增量写入 Redis: ai:task:{id}:stream
              │ 3. 完成后写 ai_task_result
              ▼
       前端 SSE / 轮询拿到 token,渲染流式输出
```

### 3.3 调用契约

Java → Python 统一约定:

```http
POST /v1/{capability}/{action}
Content-Type: application/json
X-Trace-Id: {uuid}              # 全链路追踪
X-Request-Id: {uuid}
X-User-Id: {uid}                # 透传用户标识 (审计)
Authorization: Bearer {internal_token}   # 服务间内部令牌

{
  "task_id": "...",
  "stream": true|false,
  "payload": { ... 业务参数 ... }
}
```

返回 (非流式):

```json
{
  "code": 0,
  "msg": "ok",
  "data": { ... },
  "trace_id": "..."
}
```

返回 (流式 SSE):

```
event: token
data: {"delta":"我"}

event: token
data: {"delta":"是"}

event: done
data: {"finish_reason":"stop","usage":{...}}
```

---

## 4. 端到端数据流 (以"简历优化"为例)

```
[1] 用户上传简历 PDF
    Web ──► Java /api/resume/upload
        ├─ 存 MinIO: resume/{userId}/{uuid}.pdf
        └─ 落库 resume (file_url, status=UPLOADED)

[2] 用户选择目标 JD,点击"AI 优化"
    Web ──► Java /api/resume/optimize {resumeId, jdId}
        ├─ 写 ai_task (PENDING) → 返回 task_id
        └─ 推 Redis Stream

[3] Java Worker 消费任务
    ├─ 读 resume 文本 + jd 文本
    ├─ POST Python /v1/resume/optimize (stream=true)
    └─ 透传 token → Redis ai:task:{id}:stream

[4] Python 处理
    ├─ LangGraph: parse_resume → match_jd → rewrite → review
    ├─ RAG: 从 FAISS 检索相似优秀简历片段作为 few-shot
    ├─ LLM: 流式生成
    └─ 持久化 embedding (可选,用于相似度复用)

[5] 前端 SSE 接收
    ├─ 实时渲染优化后的内容
    └─ 完成后 GET /api/task/{id} 拿到完整结果 + diff
```

---

## 5. 关键非功能性设计

| 维度 | 方案 |
| --- | --- |
| **可用性** | Java/Python 均可水平扩展;LLM 调用熔断 (Resilience4j / tenacity);本地兜底模型 |
| **一致性** | AI 任务采用最终一致;关键状态以 `ai_task` 表为唯一真相源 (Source of Truth) |
| **限流** | Nginx 层 IP 限流 + Java 用户级令牌桶 (Redis Lua) + Python 模型级并发信号量 |
| **幂等** | 所有 POST /v1/* 必带 `request_id`,Python 侧用 Redis SETNX 去重 (TTL 10min) |
| **追踪** | `X-Trace-Id` 贯穿 Nginx → Java → Python → LLM,日志统一打 traceId |
| **安全** | JWT (前端 ↔ Java) + 内部 HMAC Token (Java ↔ Python);敏感字段脱敏后再入 Prompt |
| **成本** | LLM 调用按用户配额 + 命中缓存 (相同 input hash → Redis 24h);批量任务降级到便宜模型 |

