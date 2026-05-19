# 06 - 企业级目录结构

本文档对应需求中的 **14. 企业级目录结构**,给出完整、可直接 copy 落地的目录骨架。

---

## 1. 顶层结构(Monorepo)

```
agent-jd/
├── README.md
├── LICENSE
├── .editorconfig
├── .gitignore
├── .gitattributes
├── .gitleaks.toml
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── release.yml
│       └── security.yml
│
├── docs/                                # 架构与设计文档
│   ├── 01-architecture.md
│   ├── 02-java-backend.md
│   ├── 03-python-agent.md
│   ├── 04-storage-design.md
│   ├── 05-deployment.md
│   └── 06-directory.md
│
├── deploy/                              # 部署相关
│   ├── docker/
│   │   ├── java.Dockerfile
│   │   ├── python.Dockerfile
│   │   └── web.Dockerfile
│   ├── docker-compose/
│   │   ├── infra.yml                    # 仅基础设施 (mysql/redis/minio)
│   │   ├── dev.yml                      # 开发用,挂载本地代码
│   │   └── all.yml                      # 完整部署
│   ├── nginx/
│   │   ├── nginx.conf
│   │   ├── conf.d/
│   │   │   └── agent-jd.conf
│   │   └── web.conf
│   ├── k8s/                             # (可选) K8s 资源
│   │   ├── base/
│   │   ├── overlays/dev/
│   │   ├── overlays/stage/
│   │   └── overlays/prod/
│   ├── sql/
│   │   ├── init.sql                     # 初始化 schema
│   │   └── migrations/                  # Flyway / Liquibase
│   │       ├── V1__init.sql
│   │       └── V2__add_match_table.sql
│   └── env/
│       ├── .env.dev.example
│       ├── .env.stage.example
│       └── .env.prod.example
│
├── agent-jd-java/                       # Java 主业务后端
├── agent-jd-python/                     # Python Agent 服务
└── agent-jd-web/                        # Vue3 前端
```

---

## 2. Java 后端目录(`agent-jd-java/`)

```
agent-jd-java/
├── pom.xml                              # 父 POM,锁版本 + 公共插件
├── mvnw / mvnw.cmd
├── .mvn/
├── checkstyle.xml
├── spotless.xml
│
├── agent-jd-common/                     # 通用工具
│   └── src/main/java/com/agentjd/common/
│       ├── result/Result.java
│       ├── result/PageResult.java
│       ├── exception/BizException.java
│       ├── exception/ErrorCode.java
│       ├── annotation/RequirePerm.java
│       ├── annotation/RateLimit.java
│       ├── annotation/Idempotent.java
│       ├── util/JsonUtils.java
│       ├── util/SnowflakeIdWorker.java
│       └── constants/Constants.java
│
├── agent-jd-framework/                  # 框架增强
│   └── src/main/java/com/agentjd/framework/
│       ├── web/GlobalExceptionHandler.java
│       ├── web/ResponseAdvice.java
│       ├── web/CorsConfig.java
│       ├── trace/TraceFilter.java
│       ├── trace/TraceContext.java
│       ├── log/AccessLogAspect.java
│       ├── ratelimit/RateLimitAspect.java
│       ├── idempotent/IdempotentAspect.java
│       └── config/JacksonConfig.java
│
├── agent-jd-security/                   # 鉴权
│   └── src/main/java/com/agentjd/security/
│       ├── jwt/JwtService.java
│       ├── jwt/JwtAuthFilter.java
│       ├── jwt/UserContextHolder.java
│       ├── perm/PermissionAspect.java
│       └── config/SecurityConfig.java
│
├── agent-jd-storage/                    # 文件存储
│   └── src/main/java/com/agentjd/storage/
│       ├── ObjectStorage.java           # 抽象接口
│       ├── minio/MinioObjectStorage.java
│       ├── oss/AliyunOssObjectStorage.java
│       └── config/StorageProperties.java
│
├── agent-jd-cache/                      # Redis 封装
│   └── src/main/java/com/agentjd/cache/
│       ├── RedisService.java
│       ├── DistributedLock.java
│       ├── RateLimiter.java             # Lua 令牌桶
│       ├── Idempotency.java
│       ├── stream/StreamProducer.java
│       ├── stream/StreamConsumer.java
│       └── config/RedisConfig.java
│
├── agent-jd-agent-client/               # 调 Python Agent
│   └── src/main/java/com/agentjd/agent/client/
│       ├── AgentApi.java                # 接口
│       ├── AgentClient.java             # WebClient 实现
│       ├── AgentProperties.java
│       ├── dto/                         # 请求/响应 DTO
│       │   ├── JdAnalyzeReq.java
│       │   ├── JdAnalysisDTO.java
│       │   ├── ResumeOptimizeReq.java
│       │   ├── ProjectRewriteReq.java
│       │   ├── MatchReq.java
│       │   ├── MatchScoreDTO.java
│       │   ├── GreetingReq.java
│       │   ├── GreetingDTO.java
│       │   ├── TaskAck.java
│       │   └── TokenChunk.java
│       ├── interceptor/HmacSigner.java
│       ├── retry/RetryConfig.java
│       └── circuit/CircuitConfig.java
│
├── agent-jd-domain/                     # 领域模块(每个域独立子模块)
│   ├── pom.xml                          # 聚合
│   ├── domain-user/
│   │   └── src/main/java/com/agentjd/user/
│   │       ├── interfaces/controller/AuthController.java
│   │       ├── interfaces/controller/UserController.java
│   │       ├── interfaces/dto/...
│   │       ├── application/AuthAppService.java
│   │       ├── application/UserAppService.java
│   │       ├── domain/model/User.java
│   │       ├── domain/model/UserQuota.java
│   │       ├── domain/repository/UserRepository.java
│   │       ├── domain/service/PasswordService.java
│   │       └── infrastructure/
│   │           ├── persistence/po/UserPO.java
│   │           ├── persistence/mapper/UserMapper.java
│   │           ├── persistence/UserRepositoryImpl.java
│   │           └── converter/UserConverter.java
│   │
│   ├── domain-resume/
│   │   └── src/main/java/com/agentjd/resume/
│   │       ├── interfaces/controller/ResumeController.java
│   │       ├── application/ResumeAppService.java
│   │       ├── application/ResumeOptimizeAppService.java   # 调 Python
│   │       ├── application/ProjectRewriteAppService.java
│   │       ├── domain/model/Resume.java
│   │       ├── domain/model/ResumeSection.java
│   │       ├── domain/model/ResumeVersion.java
│   │       ├── domain/repository/ResumeRepository.java
│   │       └── infrastructure/...
│   │
│   ├── domain-jd/
│   │   └── src/main/java/com/agentjd/jd/
│   │       ├── interfaces/controller/JdController.java
│   │       ├── application/JdAppService.java
│   │       ├── application/JdAnalyzeAppService.java
│   │       ├── domain/model/Jd.java
│   │       ├── domain/model/JdAnalysis.java
│   │       └── infrastructure/...
│   │
│   ├── domain-match/
│   │   └── src/main/java/com/agentjd/match/
│   │       ├── interfaces/controller/MatchController.java
│   │       ├── application/MatchAppService.java
│   │       ├── domain/model/MatchRecord.java
│   │       └── infrastructure/...
│   │
│   ├── domain-greeting/
│   │   └── src/main/java/com/agentjd/greeting/
│   │       ├── interfaces/controller/GreetingController.java
│   │       ├── application/GreetingAppService.java
│   │       └── infrastructure/...
│   │
│   ├── domain-ai-task/                  # 任务中枢(被其它域引用)
│   │   └── src/main/java/com/agentjd/aitask/
│   │       ├── interfaces/controller/TaskController.java
│   │       ├── interfaces/sse/TaskSseController.java
│   │       ├── application/AiTaskAppService.java
│   │       ├── application/AiTaskOrchestrator.java        # 编排"创建→入队→回写"
│   │       ├── domain/model/AiTask.java
│   │       ├── domain/model/AiTaskStatus.java
│   │       ├── domain/repository/AiTaskRepository.java
│   │       └── infrastructure/
│   │           ├── persistence/...
│   │           └── stream/AiTaskProducer.java
│   │
│   ├── domain-file/
│   │   └── src/main/java/com/agentjd/file/
│   │       ├── interfaces/controller/FileController.java
│   │       └── application/FileAppService.java
│   │
│   └── domain-system/
│       └── src/main/java/com/agentjd/system/
│           ├── interfaces/controller/DictController.java
│           ├── interfaces/controller/ConfigController.java
│           └── domain/model/...
│
├── agent-jd-admin/                      # ✦ 启动模块 (HTTP 服务)
│   ├── pom.xml                          # 依赖所有 domain-*
│   └── src/main/
│       ├── java/com/agentjd/admin/AdminApplication.java
│       └── resources/
│           ├── application.yml
│           ├── application-dev.yml
│           ├── application-stage.yml
│           ├── application-prod.yml
│           ├── logback-spring.xml
│           ├── i18n/messages_zh.properties
│           └── db/migration/            # Flyway
│               └── V1__init.sql
│
└── agent-jd-worker/                     # ✦ 启动模块 (异步 Worker)
    ├── pom.xml
    └── src/main/
        ├── java/com/agentjd/worker/
        │   ├── WorkerApplication.java
        │   └── consumer/AiTaskConsumer.java   # 消费 Redis Stream → 调 Python → 回写
        └── resources/
            ├── application.yml
            └── application-worker.yml
```

> **设计要点**
> - `admin` 与 `worker` 仅在 `resources/application*.yml` 不同;Spring `@Profile("worker")` 控制是否启用消费者 bean。
> - `domain-*` 互不依赖(只能依赖 common/framework/cache/agent-client);跨域协作走 `application` 层 API,不直连别人的 Repository。
> - `domain-ai-task` 是被多域引用的中枢,允许其它域 import 其 `application` 接口。

---

## 3. Python Agent 目录(`agent-jd-python/`)

```
agent-jd-python/
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .python-version
├── ruff.toml
├── mypy.ini
├── Makefile
├── README.md
│
├── app/
│   ├── main.py                          # FastAPI 入口
│   ├── api/
│   │   ├── deps.py                      # 依赖注入(auth/tracing/idempotency)
│   │   ├── v1/
│   │   │   ├── __init__.py              # 路由聚合
│   │   │   ├── health.py
│   │   │   ├── resume.py
│   │   │   ├── jd.py
│   │   │   ├── match.py
│   │   │   └── greeting.py
│   │   └── schemas/
│   │       ├── common.py                # BaseResp / ErrorResp
│   │       ├── resume.py
│   │       ├── jd.py
│   │       ├── match.py
│   │       └── greeting.py
│   │
│   ├── agents/                          # LangGraph 工作流
│   │   ├── base.py                      # BaseGraph、State 基类
│   │   ├── resume_optimize_graph.py
│   │   ├── project_rewrite_graph.py
│   │   ├── jd_analyze_graph.py
│   │   ├── match_graph.py
│   │   └── greeting_graph.py
│   │
│   ├── chains/                          # 可复用 LCEL 链
│   │   ├── extract_skills.py
│   │   ├── rewrite_star.py
│   │   ├── score_match.py
│   │   └── safety_filter.py
│   │
│   ├── tools/                           # Function Tools
│   │   ├── resume_parser.py
│   │   ├── jd_retriever.py
│   │   ├── skill_dict.py
│   │   └── scorer.py
│   │
│   ├── rag/
│   │   ├── loader.py
│   │   ├── splitter.py
│   │   ├── embedder.py
│   │   ├── vectorstore.py               # FaissStore
│   │   ├── retriever.py                 # Hybrid (vec + bm25)
│   │   └── reindex_job.py
│   │
│   ├── prompts/
│   │   ├── __init__.py                  # PromptRegistry
│   │   ├── loader.py
│   │   └── templates/
│   │       ├── resume_optimize/
│   │       │   ├── v1.yaml
│   │       │   ├── v2.yaml
│   │       │   └── v2.examples.json
│   │       ├── project_rewrite/v1.yaml
│   │       ├── jd_analyze/v1.yaml
│   │       ├── match/v1.yaml
│   │       └── greeting/v1.yaml
│   │
│   ├── llm/
│   │   ├── base.py                      # LLMProvider 抽象
│   │   ├── factory.py
│   │   ├── openai_provider.py
│   │   ├── dashscope_provider.py
│   │   └── embedding/
│   │       ├── base.py
│   │       ├── openai_embedding.py
│   │       └── bge_embedding.py
│   │
│   ├── core/
│   │   ├── settings.py                  # pydantic-settings
│   │   ├── logger.py                    # loguru → JSON
│   │   ├── tracing.py                   # X-Trace-Id 上下文
│   │   ├── errors.py
│   │   ├── security.py                  # HMAC 校验中间件
│   │   ├── idempotency.py
│   │   └── ratelimit.py
│   │
│   ├── infra/
│   │   ├── redis_client.py
│   │   ├── object_storage.py
│   │   └── http_client.py
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_jd_analyze.py
│       ├── test_resume_optimize.py
│       ├── test_match.py
│       └── test_prompts.py
│
├── data/
│   ├── faiss_index/                     # 持久化(挂卷)
│   │   ├── resume.index
│   │   ├── jd.index
│   │   └── ...
│   ├── faiss_meta/                      # SQLite 元数据
│   └── seed/                            # 初始语料
│       ├── resumes/
│       └── jds/
│
└── scripts/
    ├── build_faiss.py                   # 离线构建索引
    ├── reindex.py
    ├── eval_prompt.py                   # Prompt 评估脚本
    └── export_openapi.py
```

---

## 4. 前端目录(`agent-jd-web/`)

```
agent-jd-web/
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json
├── vite.config.ts
├── .eslintrc.cjs
├── .prettierrc
├── index.html
│
├── public/
│   └── favicon.svg
│
└── src/
    ├── main.ts
    ├── App.vue
    ├── router/
    │   └── index.ts
    ├── stores/                          # Pinia
    │   ├── user.ts
    │   ├── task.ts
    │   └── resume.ts
    ├── api/
    │   ├── http.ts                      # Axios 封装(拦截器、统一错误)
    │   ├── auth.ts
    │   ├── resume.ts
    │   ├── jd.ts
    │   ├── match.ts
    │   ├── greeting.ts
    │   └── task.ts                      # 包含 SSE
    ├── composables/
    │   ├── useSse.ts
    │   ├── useTaskStream.ts
    │   └── useDebounce.ts
    ├── views/
    │   ├── auth/Login.vue
    │   ├── auth/Register.vue
    │   ├── dashboard/Dashboard.vue
    │   ├── resume/ResumeList.vue
    │   ├── resume/ResumeEditor.vue      # 流式渲染优化结果
    │   ├── jd/JdList.vue
    │   ├── jd/JdAnalyzer.vue
    │   ├── match/MatchReport.vue
    │   ├── greeting/GreetingComposer.vue
    │   └── task/TaskCenter.vue
    ├── components/
    │   ├── layout/Header.vue
    │   ├── layout/Sider.vue
    │   ├── common/Loading.vue
    │   ├── common/StreamingText.vue     # SSE 流式输出组件
    │   └── chart/RadarScore.vue
    ├── styles/
    │   ├── index.scss
    │   └── element-overrides.scss
    ├── utils/
    │   ├── auth.ts
    │   ├── format.ts
    │   └── trace.ts
    └── types/
        ├── api.d.ts
        └── domain.d.ts
```

---

## 5. 命名与代码组织约定

### Java 包命名

```
com.agentjd
 ├─ common         (公共工具与基础类)
 ├─ framework      (框架增强)
 ├─ security
 ├─ storage
 ├─ cache
 ├─ agent.client
 └─ {domain}                      e.g. resume / jd / aitask
      ├─ interfaces
      ├─ application
      ├─ domain
      └─ infrastructure
```

### Python 模块命名

- 全 lowercase + underscore;包名与目录名一致。
- 跨模块共享只能 import `app.core` / `app.llm` / `app.prompts` / `app.rag`。
- `agents/*_graph.py` 内只放图定义与 State,具体节点函数下沉到 `chains/` 或 `tools/`,便于复用。

### 前端命名

- 文件:PascalCase 组件、camelCase 工具。
- API 函数与后端 path 一一映射;`api/resume.ts` 提供 `optimizeResume(id, payload)` 等方法。

---

## 6. 落地顺序建议

1. **先搭骨架**:按本目录结构创建空文件 / 空类 + `application.yml` + `pyproject.toml`,跑通 Hello World。
2. **打通基础设施**:`docker-compose -f deploy/docker-compose/infra.yml up -d` → MySQL/Redis/MinIO 就绪。
3. **打通认证链路**:Java 注册/登录 → JWT → 前端登录页。
4. **打通 Agent 链路**:Python `/v1/health` → Java `AgentClient` 健康检查 → 前端展示。
5. **跑通一个最小用例**:JD 分析(同步),覆盖 Java → Python → LLM → 落库的完整路径。
6. **加上异步任务**:简历优化 → Redis Stream → Worker → 流式 SSE 回前端。
7. **接入 RAG**:`scripts/build_faiss.py` 灌种子语料,把简历优化升级为带 few-shot 的版本。
8. **完善其它能力**:项目改写、匹配度、打招呼。
9. **可观测性 + 安全 + 限流配额**。
10. **CI/CD + Docker 完整部署**。

