# AI 求职 Agent 平台（agent-jd）

一个面向求职场景的全栈 AI 应用原型。项目使用 Spring Boot 管理用户、简历、JD、文件、会话和 AI 任务，使用 FastAPI + LangGraph 承载大模型工作流，前端使用 Vue 3 提供完整交互页面。

> 当前版本定位为可运行、可评测的个人项目。生产级任务队列、SSE、容器化全量部署和可观测性仍在 Roadmap 中，不作为已完成功能描述。

## 已实现能力

| 能力 | 当前实现 |
| --- | --- |
| 简历优化 | 简历/JD 输入校验、结构化解析、匹配分析、RAG 增强、建议生成与输出校验 |
| JD 分析 | 技能关键词、软技能、加分项和岗位方向提取 |
| 项目改写 | 根据目标 JD 与知识库参考生成 STAR 描述和简历 bullet |
| 岗位匹配 | 规则初算 + LLM 结构化分析，输出匹配项、缺口、优势和风险 |
| 多轮对话 | Redis 会话上下文、上下文窗口裁剪和 Prompt 缓存 |
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

## 快速启动

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
pip install -r requirements.txt -r requirements-embedding.txt
python -m scripts.import_knowledge
uvicorn app.main:app --reload --port 8000
```

调用真实大模型前，需要在 `.env` 中设置对应 API Key。中文 Embedding 依赖被单独放在 `requirements-embedding.txt`，避免基础测试环境安装 CUDA 版本 PyTorch；模型首次运行时会从 Hugging Face 下载。

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

## 当前边界

- Java AI 任务目前使用进程内异步执行和前端轮询，不具备服务重启后的可靠恢复能力。
- Agent 工作流已支持简历优化场景的条件路由和有限重试，其他能力仍以固定工作流为主。
- FAISS 索引适合单机演示；多实例并发写和生产级索引管理尚未实现。
- `docs/` 中关于 Redis Stream、SSE、MinIO、Kubernetes、监控和 CI/CD 的内容属于演进设计，不代表当前均已落地。

## Roadmap

- [ ] Redis Stream / RabbitMQ 可靠任务队列与幂等消费
- [ ] SSE 流式进度、断线重连和事件回放
- [ ] Reranker、离线评测报告和答案忠实度评测
- [ ] PII 脱敏、Prompt Injection 防护、调用配额与审计
- [ ] Java/Python/Web 全量 Dockerfile 与 GitHub Actions
- [ ] LangGraph Checkpoint、Human-in-the-loop 和更多条件路由
