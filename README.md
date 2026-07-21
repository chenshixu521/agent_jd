# AI 求职 Agent 平台（agent-jd）

[![CI](https://github.com/chenshixu521/agent_jd/actions/workflows/ci.yml/badge.svg)](https://github.com/chenshixu521/agent_jd/actions/workflows/ci.yml)

一个面向求职场景的全栈 AI 应用原型。项目使用 Spring Boot 管理用户、简历、JD、文件、会话和 AI 任务，使用 FastAPI + LangGraph 承载大模型工作流，前端使用 Vue 3 提供完整交互页面。

> 当前版本定位为可运行、可评测的个人项目，支持 Docker Compose 一键启动。多实例高吞吐任务调度、SSE 和可观测性仍在 Roadmap 中，不作为已完成功能描述。

## 已实现能力

| 能力 | 当前实现 |
| --- | --- |
| 简历优化 | 简历/JD 输入校验、结构化解析、匹配分析、RAG 增强、建议生成与输出校验 |
| JD 分析 | 技能关键词、软技能、加分项和岗位方向提取 |
| 项目改写 | 根据目标 JD 与知识库参考生成 STAR 描述和简历 bullet |
| 岗位匹配 | 规则初算 + LLM 结构化分析，输出匹配项、缺口、优势和风险 |
| 多轮对话 | Redis 会话上下文、上下文窗口裁剪和 Prompt 缓存 |
| 可靠任务 | Redis Stream 消费组、幂等锁、自动重试、Pending 恢复和死信队列 |
| 文档处理 | PDF、DOCX、TXT 上传与文本提取 |
| RAG | 多知识库切分、中文 Embedding、FAISS 向量召回、BM25 召回和 RRF 融合 |

## 技术栈

- Java：Java 17、Spring Boot 3、MyBatis-Plus、MySQL、Redis、JWT、WebClient
- Python：Python 3.11、FastAPI、LangGraph、Pydantic、FAISS、sentence-transformers
- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia、Axios
- 本地基础设施：Docker Compose、MySQL 8、Redis 7

## 核心链路

```text
简历 + JD
    ↓
输入完整性校验 ── 信息不足 ──> 返回澄清问题
    ↓
简历/JD 结构化解析
    ↓
FAISS 向量召回 + BM25 关键词召回 + RRF 融合
    ↓
岗位匹配分析
    ↓
简历优化建议生成
    ↓
事实与格式校验 ── 不通过 ──> 携带反馈有限重试
    ↓
结构化结果 + RAG 来源
```

## 目录结构

```text
agent-jd/
├── compose.yaml                # 完整服务编排
├── .env.example                # Docker 统一环境变量
├── agent-jd-java/              # Spring Boot 业务后端
├── agent-jd-python/            # FastAPI + LangGraph Agent 服务
│   ├── app/                    # 应用代码
│   ├── eval/                   # RAG / Agent 评测数据
│   ├── scripts/                # 导入与评测脚本
│   └── seed/                   # 示例知识库
├── agent-jd-web/               # Vue 3 前端
├── deploy/
│   ├── docker-compose/         # 本地基础设施
│   └── sql/                    # MySQL 初始化 SQL
└── docs/                       # 设计文档（包含部分 Roadmap 方案）
```

## Docker 一键启动

准备 Docker 24+ 和 Docker Compose v2，然后执行：

```bash
cp .env.example .env
# 编辑 .env，至少配置一个真实的模型 API Key
docker compose up -d --build
```

首次启动会构建 Java、Python、Web 镜像，下载中文 Embedding 模型并导入种子知识库。模型和运行数据保存在 Docker Volume，后续重启不会重复下载。

访问：<http://localhost:3000>

```bash
# 查看状态和日志
docker compose ps
docker compose logs -f python java

# 停止服务，保留数据
docker compose down
```

未配置模型 API Key 时，注册、登录、简历/JD 管理等业务功能仍可使用，AI 任务会返回配置错误。修改 `WEB_PORT` 可以更换前端端口。

## 本地开发

### 1. 启动 MySQL 与 Redis

```bash
docker compose -f deploy/docker-compose/infra.yml up -d
```

默认连接信息：

- MySQL：`localhost:3306/agent_jd`，用户 `root`，密码 `agent_jd`
- Redis：`localhost:6379`，无密码

### 2. 启动 Python Agent

```bash
cd agent-jd-python
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install --no-deps -r requirements-torch-cpu.txt
pip install -r requirements.txt -r requirements-embedding.txt
python -m scripts.import_knowledge
uvicorn app.main:app --reload --port 8000
```

调用真实大模型前，需要在 `.env` 中设置对应 API Key。CPU PyTorch 与中文 Embedding 依赖分别放在独立 requirements 文件中，基础测试环境无需安装模型依赖；模型首次运行时会从 Hugging Face 下载。

### 3. 启动 Java 后端

```bash
cd agent-jd-java
cp .env.example .env
set -a && source .env && set +a
mvn spring-boot:run
```

### 4. 启动前端

```bash
cd agent-jd-web
npm install
npm run dev
```

访问：<http://localhost:5173>

## RAG 评测

```bash
cd agent-jd-python
python -m scripts.eval_rag --provider hash
python -m scripts.eval_rag --provider sentence_transformers
```

评测脚本输出 Recall@3、Recall@5 和 MRR。`hash` 用于快速回归测试，`sentence_transformers` 用于验证实际中文语义召回效果。

## 测试

```bash
# Python
cd agent-jd-python && pip install -r requirements-dev.txt && pytest

# Java（需要 Java 17、MySQL 和 Redis）
cd agent-jd-java && mvn test

# Web
cd agent-jd-web && npm run build
```

推送到 `main` 或创建 Pull Request 时，GitHub Actions 会自动执行以上检查，并验证 Compose 配置和三个应用镜像的 Docker 构建。

AI 任务提交后先持久化到 MySQL，再写入 Redis Stream。Java Worker 使用消费组处理任务；超时、限流和服务端异常等可重试故障会保留在 Pending 列表中，超过阈值后写入 `ai:task:dlq`，鉴权和参数错误则直接失败。数据库恢复扫描会重新投递未入队的任务，Python Agent 按 `taskId` 复用已完成结果，避免重试重复调用模型。

## 当前边界

- AI 任务已支持 Redis Stream 可靠消费与重启恢复，前端进度展示目前仍使用轮询。
- Agent 工作流已支持简历优化场景的条件路由和有限重试，其他能力仍以固定工作流为主。
- FAISS 索引适合单机演示；多实例并发写和生产级索引管理尚未实现。
- `docs/` 中关于 SSE、MinIO、Kubernetes 和监控的内容属于演进设计，不代表当前均已落地。

## Roadmap

- [x] Redis Stream 可靠任务队列、幂等消费、自动重试与死信队列
- [ ] SSE 流式进度、断线重连和事件回放
- [ ] Reranker、离线评测报告和答案忠实度评测
- [ ] PII 脱敏、Prompt Injection 防护、调用配额与审计
- [x] Java/Python/Web Dockerfile 与 Docker Compose 一键部署
- [x] GitHub Actions 自动测试与镜像构建
- [ ] LangGraph Checkpoint、Human-in-the-loop 和更多条件路由
