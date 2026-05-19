# 02 - Java 主业务后端架构

本文档对应需求中的 **2. Java 后端架构 / 6. 模块划分(Java 部分)**。

---

## 1. 模块划分 (Maven 多模块)

```
agent-jd-java/
├── pom.xml                       # 父 POM,统一依赖版本
├── agent-jd-common/              # 工具、通用 DTO、错误码、注解
├── agent-jd-framework/           # 框架增强 (异常处理、拦截器、AOP、配置)
├── agent-jd-security/            # 鉴权 (JWT/Sa-Token)、权限注解
├── agent-jd-storage/             # MinIO/OSS 抽象 + 实现
├── agent-jd-cache/               # Redis 操作封装、分布式锁、限流
├── agent-jd-agent-client/        # 调用 Python Agent 的 HTTP 客户端
├── agent-jd-domain/              # 领域模块 (按业务子域聚合)
│   ├── user/                     #   用户域
│   ├── resume/                   #   简历域
│   ├── jd/                       #   岗位 JD 域
│   ├── ai-task/                  #   AI 任务域
│   └── greeting/                 #   打招呼域
├── agent-jd-admin/               # 启动模块 (Web 入口),组装所有 domain
└── agent-jd-worker/              # 异步任务 Worker 启动模块 (可独立部署)
```

> **设计要点**
> - `domain/*` 每个子域内部分 `interfaces / application / domain / infrastructure` 四层。
> - `admin` 与 `worker` 均依赖 `domain/*`,但启动方式不同;一个对外提供 HTTP,一个常驻消费 Redis Stream。
> - `agent-jd-agent-client` 不感知具体业务,仅暴露 `AgentApi` 接口。

---

## 2. 单个领域模块的内部结构 (以 `resume` 为例)

```
agent-jd-domain/resume/
├── pom.xml
└── src/main/java/com/agentjd/resume/
    ├── interfaces/
    │   ├── controller/
    │   │   └── ResumeController.java
    │   ├── dto/
    │   │   ├── request/ResumeUploadReq.java
    │   │   └── response/ResumeVO.java
    │   └── assembler/ResumeAssembler.java
    ├── application/
    │   ├── ResumeAppService.java          # 用例编排
    │   └── command/OptimizeResumeCmd.java
    ├── domain/
    │   ├── model/Resume.java               # 聚合根
    │   ├── model/ResumeStatus.java         # 枚举
    │   ├── repository/ResumeRepository.java   # 接口
    │   └── service/ResumeDomainService.java
    └── infrastructure/
        ├── persistence/
        │   ├── po/ResumePO.java
        │   ├── mapper/ResumeMapper.java   # MyBatis-Plus
        │   └── ResumeRepositoryImpl.java
        └── converter/ResumeConverter.java  # PO ↔ Domain (MapStruct)
```

---

## 3. 业务模块清单

| 模块 | 主要表 | 主要接口 | 说明 |
| --- | --- | --- | --- |
| **user** | `user`, `user_profile`, `user_quota` | `/api/auth/login`、`/api/auth/register`、`/api/user/me` | 注册、登录、JWT 刷新、配额 |
| **resume** | `resume`, `resume_section`, `resume_version` | `/api/resume/*` | 简历 CRUD、上传、解析、版本 |
| **jd** | `jd`, `jd_analysis` | `/api/jd/*` | JD 录入、AI 解析结果 |
| **ai-task** | `ai_task`, `ai_task_result`, `ai_task_event` | `/api/task/*` | 任务状态、SSE、结果查询 |
| **greeting** | `greeting_template`, `greeting_record` | `/api/greeting/*` | 打招呼模板与生成记录 |
| **match** | `match_record` | `/api/match/*` | 简历 ↔ JD 匹配评分历史 |
| **file** | `file_object` | `/api/file/*` | 文件上传/下载/预签名 URL |
| **system** | `dict`, `config`, `audit_log` | `/api/system/*` | 字典、配置、审计日志 |

---

## 4. 关键技术组件

### 4.1 鉴权: JWT + Sa-Token (二选一)

- **登录**:`POST /api/auth/login` → 校验密码 → 签发 `access_token` (15min) + `refresh_token` (7d)
- **拦截器**:`AuthInterceptor` 解析 token,放入 `UserContextHolder` (ThreadLocal)
- **权限注解**:`@RequirePerm("resume:write")`,基于 RBAC

### 4.2 异常体系

```java
public class BizException extends RuntimeException {
    private final ErrorCode code;
    // ...
}

public enum ErrorCode {
    OK(0, "ok"),
    PARAM_INVALID(40001, "参数错误"),
    AUTH_REQUIRED(40101, "未登录"),
    AGENT_TIMEOUT(50301, "AI 服务超时"),
    LLM_QUOTA_EXCEEDED(50302, "AI 配额已用完"),
    // ...
}
```

`@RestControllerAdvice` 统一捕获 → 返回 `Result<T>`:

```json
{ "code": 50301, "msg": "AI 服务超时", "data": null, "traceId": "..." }
```

### 4.3 调用 Python Agent: `AgentClient`

```java
public interface AgentApi {
    AgentResp<JdAnalysisDTO> analyzeJd(JdAnalyzeReq req);
    AgentResp<TaskAck> optimizeResume(ResumeOptimizeReq req);     // 异步,返回 task_id
    Flux<TokenChunk> streamResumeOptimize(String taskId);          // SSE
    AgentResp<MatchScoreDTO> matchScore(MatchReq req);
    AgentResp<GreetingDTO> generateGreeting(GreetingReq req);
    AgentResp<RewriteDTO> rewriteProject(ProjectRewriteReq req);
}
```

实现使用 `WebClient` (Reactor),配置:
- `connectTimeout=3s`、`responseTimeout=120s`
- 重试:幂等接口 (analyze/match) 指数退避 3 次
- 熔断:Resilience4j,失败率 50% 打开,30s 半开
- 内部 Token:`X-Internal-Token`,HMAC-SHA256(payload + timestamp, shared_secret)

### 4.4 异步任务: Redis Stream

```
ai:task:queue              # Stream key
ai:task:{taskId}            # Hash: status / progress
ai:task:{taskId}:stream     # List: token chunks for SSE replay
```

Worker:
```java
@Component
public class AiTaskConsumer {
    @Scheduled(fixedDelay = 100)
    public void consume() {
        // XREADGROUP GROUP worker c1 COUNT 10 BLOCK 1000 STREAMS ai:task:queue >
        // 处理任务 → 调 AgentApi → 流式回写 Redis → ACK
    }
}
```

### 4.5 文件存储

- 上传:前端 → Java 预签名 → 直传 MinIO(避免大文件穿透 Java)
- 下载:Java 生成临时签名 URL,有效期 5min
- 路径规范:`{bucket}/resume/{userId}/{yyyyMM}/{uuid}.{ext}`

### 4.6 限流与配额

- **接口级**:Nginx `limit_req_zone` (IP 维度)
- **用户级**:Redis Lua 令牌桶,key = `rl:{uid}:{api}`
- **AI 配额**:`user_quota` 表 + Redis 计数(每日重置),超额返回 `LLM_QUOTA_EXCEEDED`

---

## 5. 主要 API 列表 (节选)

| Method | Path | 说明 |
| --- | --- | --- |
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/refresh` | 刷新 token |
| GET  | `/api/user/me` | 当前用户信息与配额 |
| POST | `/api/resume/upload` | 上传简历(返回 fileId) |
| POST | `/api/resume` | 创建简历(结构化) |
| GET  | `/api/resume/{id}` | 详情 |
| POST | `/api/resume/{id}/optimize` | **触发 AI 优化** → task_id |
| POST | `/api/resume/{id}/project/rewrite` | **触发项目改写** → task_id |
| POST | `/api/jd` | 录入 JD |
| POST | `/api/jd/{id}/analyze` | **JD 分析(同步)** |
| POST | `/api/match` | **匹配度分析** {resumeId, jdId} |
| POST | `/api/greeting` | **生成打招呼** |
| GET  | `/api/task/{id}` | 任务状态/结果 |
| GET  | `/api/task/{id}/stream` | SSE 流式拉取 |

---

## 6. 配置项规范 (`application.yml`)

```yaml
spring:
  profiles:
    active: ${ENV:dev}
  datasource:
    url: jdbc:mysql://${MYSQL_HOST}:3306/agent_jd?useSSL=false&characterEncoding=utf8
    username: ${MYSQL_USER}
    password: ${MYSQL_PWD}
  data:
    redis:
      host: ${REDIS_HOST}
      port: 6379
      password: ${REDIS_PWD:}

agent:
  python:
    base-url: ${AGENT_BASE_URL:http://agent:8000}
    internal-secret: ${AGENT_SECRET}
    connect-timeout: 3s
    response-timeout: 120s

storage:
  minio:
    endpoint: ${MINIO_ENDPOINT}
    access-key: ${MINIO_AK}
    secret-key: ${MINIO_SK}
    bucket: agent-jd

jwt:
  secret: ${JWT_SECRET}
  access-ttl: 900
  refresh-ttl: 604800
```

---

## 7. 可观测性

- **日志**:Logback + JSON 格式,包含 `traceId`、`uid`、`api`、`latencyMs`
- **指标**:Micrometer + Prometheus,关键指标:
  - `agent_call_seconds{api,outcome}` 调 Python 耗时
  - `ai_task_queue_size` Redis Stream 待消费数量
  - `llm_quota_used{uid}` 用户配额使用
- **链路**:OpenTelemetry,`X-Trace-Id` 贯穿前后端
- **审计**:`audit_log` 表记录敏感操作 (登录、配额变更、AI 任务创建)

