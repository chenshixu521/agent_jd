# AI 求职 Agent 平台 (agent-jd)

> 一个基于 **Spring Boot + LangGraph** 的企业级 AI 求职智能体平台。
>
> **Java 主业务后端** 负责用户、简历、JD、任务、文件、权限等核心业务能力;
> **Python Agent 服务** 负责 Prompt、RAG、Agent 工作流、大模型推理等智能能力;
> 前端使用 **Vue3 + Element Plus + Axios** 提供交互界面。

---

## 一、核心能力

| 能力 | 说明 |
| --- | --- |
| AI 简历优化 | 基于岗位 JD 与用户简历,生成结构化优化建议与重写后的简历 |
| 岗位 JD 分析 | 解析 JD 中的硬性技能、软性技能、加分项、隐藏诉求 |
| AI 项目改写 | 针对项目经验,按 STAR 法则 + 岗位需求重写 |
| AI 打招呼生成 | 个性化打招呼文案 (Boss、猎聘、内推等场景) |
| 岗位匹配分析 | 简历 vs JD 匹配度评分、缺口分析、补强建议 |

---

## 二、技术栈

### 1. Java 主业务后端
- Java 17、Spring Boot 3.x、Spring MVC
- MyBatis-Plus、MySQL 8、Redis 7
- Sa-Token / JWT、Knife4j (OpenAPI)
- WebClient / OpenFeign (调用 Python Agent)

### 2. Python Agent 服务
- Python 3.11、FastAPI、Uvicorn
- LangChain、**LangGraph** (Agent 工作流编排)
- OpenAI API / 通义千问 API (可切换)
- FAISS (向量检索)、sentence-transformers / bge-m3 (Embedding)
- Pydantic v2、loguru

### 3. 前端
- Vue3 + Vite、Element Plus、Pinia、Axios、TypeScript
- 工程目录: `agent-jd-web`

### 4. 基础设施
- Docker、Docker Compose、Nginx
- (可选) Prometheus + Grafana、ELK、SkyWalking

---

## 三、文档索引

所有架构设计文档位于 `docs/` 目录:

| 文档 | 内容 |
| --- | --- |
| [`docs/01-architecture.md`](docs/01-architecture.md) | 系统整体架构、调用流程、数据流 |
| [`docs/02-java-backend.md`](docs/02-java-backend.md) | Java 主业务后端架构与模块划分 |
| [`docs/03-python-agent.md`](docs/03-python-agent.md) | Python Agent 服务架构、Agent 工作流、Prompt 管理 |
| [`docs/04-storage-design.md`](docs/04-storage-design.md) | MySQL / Redis / FAISS 设计 |
| [`docs/05-deployment.md`](docs/05-deployment.md) | Docker 部署架构、工程化、CI/CD |
| [`docs/06-directory.md`](docs/06-directory.md) | 企业级目录结构 |

---

## 四、目录结构 (顶层)

```
agent-jd/
├── docs/                       # 架构与设计文档
├── agent-jd-java/              # Java 主业务后端 (Maven 多模块)
├── agent-jd-python/            # Python Agent 服务
├── agent-jd-web/               # Vue3 前端
├── deploy/                     # 部署相关
│   ├── docker/                 # Dockerfile
│   ├── docker-compose/         # docker-compose 编排
│   ├── nginx/                  # 网关配置
│   └── sql/                    # 初始化 SQL
├── .github/                    # CI/CD (或 .gitlab-ci.yml)
└── README.md
```

完整目录结构详见 [`docs/06-directory.md`](docs/06-directory.md)。

---

## 五、快速启动 (开发环境)

```bash
# 1. 启动基础设施 (MySQL + Redis)
docker compose -f deploy/docker-compose/infra.yml up -d

# 2. 启动 Python Agent 服务
cd agent-jd-python
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. 启动 Java 后端
cd agent-jd-java
./mvnw spring-boot:run -pl agent-jd-admin

# 4. 启动前端
cd agent-jd-web
pnpm install && pnpm dev
```

---

## 六、设计原则

- **模块解耦**:Java 业务域与 Python AI 域强隔离,通过 HTTP/gRPC 通信
- **能力可插拔**:大模型、Embedding、向量库均通过抽象接口注入,可一键替换
- **Prompt 与代码分离**:Prompt 由 YAML/Jinja2 模板管理,支持版本与灰度
- **任务异步化**:所有 AI 任务走异步队列,Java 通过 task_id 轮询/SSE 拉结果
- **可观测性优先**:统一 traceId 贯穿 Java → Python → LLM 调用链

