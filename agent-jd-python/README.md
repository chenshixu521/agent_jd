# agent-jd-python

FastAPI + LangGraph 的 AI 求职 Agent 服务，负责模型调用、工作流编排、RAG 检索和 Redis 会话上下文。

## 已实现接口

| 能力 | 接口 |
| --- | --- |
| 简历解析 / 优化 | `POST /v1/resume/{parse|optimize|advice}` |
| JD 解析 / 分析 | `POST /v1/jd/{parse|analyze}` |
| 关键词提取 | `POST /v1/keyword/extract` |
| 项目改写 | `POST /v1/project/rewrite` |
| 打招呼生成 | `POST /v1/greeting/generate` |
| 岗位匹配 | `POST /v1/match/analyze` |
| 多轮对话 | `POST /v1/chat/message` |
| RAG 管理 | `/v1/rag/*` |
| 会话管理 | `/v1/sessions/*` |

## 安装与启动

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate

# 基础服务依赖
pip install -r requirements.txt

# 使用本地中文语义 Embedding 时安装 CPU PyTorch 与 sentence-transformers
pip install --no-deps -r requirements-torch-cpu.txt
pip install -r requirements-embedding.txt

python -m scripts.import_knowledge
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`.env.example` 默认使用 `BAAI/bge-small-zh-v1.5`。如只做快速回归，可设置：

```env
EMBEDDING_PROVIDER=hash
EMBEDDING_MODEL=hash-baseline
EMBEDDING_DIMENSION=384
```

## 简历优化工作流

```text
validate_input
  ├─ 信息不足 -> clarify_input -> finalize
  └─ 信息完整
       -> parse_resume
       -> parse_jd
       -> extract_keywords
       -> rag
       -> match_analysis
       -> generate_advice
       -> validate_advice
            ├─ 通过或达到 2 次生成 -> finalize
            └─ 未通过 -> generate_advice
```

匹配结果由 Pydantic Schema 校验，分数被限制在 0～100，并返回匹配/缺失技能的证据说明。最终结果同时返回 RAG `sources`、生成次数和校验反馈。

## RAG

当前实现包含：

- `sentence-transformers` 中文语义 Embedding，Hash Embedding 作为测试基线。
- FAISS `IndexFlatIP` 向量召回。
- 支持英文技术词、中文单字和中文 bigram 的 BM25 召回。
- Reciprocal Rank Fusion（RRF）融合向量与关键词排名。
- `kb + doc_id` 级替换更新，重复导入不会持续累积同一文档。
- 检索来源、融合排名和原始分数写入结果元数据。

支持的知识库：`jd`、`project_template`、`skill_keyword`、`interview_question`、`greeting_template`、`resume_corpus`。

导入知识：

```bash
python -m scripts.import_knowledge --file seed/knowledge.jsonl
```

运行评测：

```bash
python -m scripts.eval_rag --provider hash --details
python -m scripts.eval_rag --provider sentence_transformers --details
```

评测指标包括 Recall@3、Recall@5 和 MRR。当前数据集属于仓库内开发集，应用于回归和方案对比，不应当作真实线上业务指标。

## 请求契约

```json
{
  "taskId": "uuid",
  "stream": false,
  "payload": {
    "resume_text": "...",
    "jd_text": "..."
  }
}
```

```http
Authorization: Bearer <shared-internal-token>
X-Trace-Id: trace-id
X-User-Id: 1001
```

## 测试

```bash
pip install -r requirements-dev.txt
pytest
```

测试默认显式使用 Hash Embedding，因此不会下载本地模型。
