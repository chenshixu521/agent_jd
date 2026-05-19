# agent-jd-python

FastAPI + LangGraph 的 AI 求职 Agent 服务。

## 功能

| 能力 | 接口 |
| --- | --- |
| 解析简历 | `POST /v1/resume/parse` |
| 简历优化建议 | `POST /v1/resume/optimize` |
| 解析岗位 JD | `POST /v1/jd/analyze` |
| 技能关键词提取 | `POST /v1/keyword/extract` |
| 项目改写 | `POST /v1/project/rewrite` |
| AI 打招呼生成 | `POST /v1/greeting/generate` |
| 岗位匹配分析 | `POST /v1/match/analyze` |
| 多轮对话 | `POST /v1/chat/message` |
| 会话管理 | `/v1/sessions` |

## 项目结构

```text
agent-jd-python/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── deps.py
│   │   ├── schemas/common.py
│   │   └── v1/
│   │       ├── agent.py
│   │       └── health.py
│   ├── agents/
│   │   ├── state.py
│   │   ├── nodes.py
│   │   ├── graphs.py
│   │   └── router.py
│   ├── tools/
│   │   ├── resume_parser_tool.py
│   │   ├── jd_parser_tool.py
│   │   ├── keyword_extract_tool.py
│   │   ├── project_rewrite_tool.py
│   │   ├── greeting_generate_tool.py
│   │   └── match_analysis_tool.py
│   ├── prompts/
│   │   ├── loader.py
│   │   └── templates/
│   ├── llm/
│   ├── rag/
│   ├── infra/
│   └── core/
├── tests/
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## 请求契约

兼容 Java `AgentClient`:

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

请求头:

```http
Authorization: Bearer <shared-internal-token>
X-Trace-Id: trace-id
X-User-Id: 1001
```

响应:

```json
{
  "code": 0,
  "msg": "ok",
  "data": {},
  "traceId": "trace-id"
}
```

## 启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 示例

```bash
curl -X POST http://localhost:8000/v1/jd/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <shared-internal-token>" \
  -d '{"taskId":"demo","stream":false,"payload":{"jd_text":"招聘 Java 后端工程师，要求 Spring Boot、MySQL、Redis。"}}'
```

## Agent 工作流

- `resume/optimize`: `parse_resume -> parse_jd -> extract_keywords -> retrieve_rag -> match_analysis -> generate_advice -> finalize`
- `jd/analyze`: `parse_jd -> extract_keywords -> finalize`
- `project/rewrite`: `parse_jd -> project_rewrite -> finalize`
- `match/analyze`: `parse_resume -> parse_jd -> match_analysis -> finalize`
- `greeting/generate`: `parse_jd -> greeting_generate -> finalize`
- `chat/message`: `chat -> finalize`

## Redis 上下文

- `agent:context:{taskId}`: 保存请求、结果与上下文,TTL 24h
- `agent:event:{taskId}`: 保存节点事件列表,TTL 24h
- `agent:task:{taskId}`: 保存 Agent 任务状态,TTL 24h
- `session:state:{sessionId}`: 保存会话状态,TTL 7d
- `session:messages:{sessionId}`: 保存历史消息,TTL 7d
- `session:user:{userId}`: 保存用户会话索引,TTL 7d
- `prompt:ctx:{capability}:{version}:{hash}`: 保存 Prompt/LLM 结果缓存,TTL 默认 1h

会话 API：

```http
POST /v1/sessions
GET /v1/sessions/{sessionId}
POST /v1/sessions/{sessionId}/messages
GET /v1/sessions/{sessionId}/messages
GET /v1/sessions/{sessionId}/context
```

## FAISS

默认使用 `HashEmbedder + FAISS IndexFlatIP`，索引路径由 `FAISS_DIR` 控制。无语料时检索结果为空，但服务仍可运行。

## RAG 知识库

已支持 6 类知识库：

| KB | 内容 |
| --- | --- |
| `jd` | 岗位 JD |
| `project_template` | AI 项目模板 |
| `skill_keyword` | 技能关键词 |
| `interview_question` | 面试题 |
| `greeting_template` | 打招呼模板 |
| `resume_corpus` | 优秀简历片段 |

导入种子数据：

```bash
python scripts/import_knowledge.py --file seed/knowledge.jsonl
```

检索验证：

```bash
python scripts/rag_smoke.py
```

API：

```http
POST /v1/rag/index
POST /v1/rag/search
POST /v1/rag/prompt-context
```
