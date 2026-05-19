# 08 - RAG 模块设计与实现

本文档说明 AI 求职 Agent 平台中的 RAG 模块,对应 Python 服务 `agent-jd-python/app/rag`。

---

## 1. RAG 架构

```text
知识库原文
  ├── 岗位 JD
  ├── AI 项目模板
  ├── 技能关键词
  ├── 面试题
  └── 打招呼模板
        │
        ▼
KnowledgeDoc(kb, doc_id, text, metadata)
        │
        ▼
LangChain RecursiveCharacterTextSplitter
        │
        ▼
RagChunk(kb, doc_id, chunk_id, text, metadata)
        │
        ▼
EmbeddingProvider
  ├── HashEmbeddingProvider(默认,本地可运行)
  ├── OpenAIEmbeddingProvider
  └── DashScopeEmbeddingProvider
        │
        ▼
FAISS IndexIDMap(IndexFlatIP)
        │
        ├── {kb}.index
        └── {kb}.meta.json
        │
        ▼
RagService
  ├── search(kb)
  ├── search_multi(kbs)
  ├── recall_for_job
  ├── recall_for_project
  ├── recall_for_greeting
  └── build_prompt_context
        │
        ▼
PromptEnhancer / LangGraph 节点
```

---

## 2. 知识库划分

| KB | 内容 | 典型用途 |
| --- | --- | --- |
| `jd` | 岗位 JD 样本 | 岗位召回、JD 分析参考 |
| `project_template` | AI/后端/业务项目模板 | 项目改写、简历优化 few-shot |
| `skill_keyword` | 标准技能关键词 | 技能标准化、匹配分析 |
| `interview_question` | 面试题和回答要点 | 优化建议、面试准备 |
| `greeting_template` | 打招呼模板 | Boss/邮件/内推文案生成 |
| `resume_corpus` | 优秀简历片段 | 简历优化 few-shot |

---

## 3. 核心代码

| 文件 | 说明 |
| --- | --- |
| `app/rag/schema.py` | `KnowledgeDoc`、`RagChunk`、`RagHit` 数据模型 |
| `app/rag/splitter.py` | LangChain 文档切分 |
| `app/rag/embedding_api.py` | Embedding 抽象与 OpenAI/通义/Hash 实现 |
| `app/rag/vectorstore.py` | FAISS 持久化、多元数据检索 |
| `app/rag/service.py` | RAG 应用服务,多知识库召回与 Prompt 增强 |
| `app/rag/retriever.py` | 兼容旧调用的检索入口 |
| `app/rag/prompt_enhancer.py` | Prompt 上下文拼装 |
| `app/api/v1/rag.py` | RAG API: index/search/prompt-context |

---

## 4. FAISS 实现

每个知识库一个独立索引:

```text
FAISS_DIR/
├── jd.index
├── jd.meta.json
├── project_template.index
├── project_template.meta.json
├── skill_keyword.index
├── skill_keyword.meta.json
├── interview_question.index
├── interview_question.meta.json
├── greeting_template.index
├── greeting_template.meta.json
└── resume_corpus.index
```

默认使用:

```python
faiss.IndexIDMap(faiss.IndexFlatIP(dim))
```

所有向量归一化后使用内积近似余弦相似度。

---

## 5. Embedding 代码

默认本地可运行:

```python
HashEmbeddingProvider(dim=384)
```

生产可切换:

```env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=xxx
```

或:

```env
EMBEDDING_PROVIDER=dashscope
EMBEDDING_MODEL=text-embedding-v2
DASHSCOPE_API_KEY=xxx
```

---

## 6. 检索代码

```python
from app.rag.service import get_rag_service

service = get_rag_service()
hits = service.search_multi(
    query="Java LangGraph RAG Agent 项目",
    kbs=["jd", "project_template", "skill_keyword"],
    top_k=5,
)
```

岗位召回:

```python
hits = service.recall_for_job("Java 后端 Spring Boot Redis")
```

项目模板召回:

```python
hits = service.recall_for_project("LangGraph Agent RAG 工具调用")
```

打招呼模板召回:

```python
hits = service.recall_for_greeting("Boss Java 后端岗位")
```

---

## 7. Prompt 增强流程

```text
用户输入 / JD / 简历
        │
        ▼
构造 query
        │
        ▼
search_multi 多知识库召回
        │
        ▼
按 score 排序 + 去重
        │
        ▼
PromptEnhancer.build_context
        │
        ▼
注入 system/user prompt
        │
        ▼
LLM 生成结果
```

增强上下文示例:

```text
【RAG检索上下文】
用户查询：Java LangGraph RAG Agent 项目

[1] 知识库: project_template | 文档: tpl-ai-agent | 相似度: 0.8123
AI Agent 项目模板：基于 FastAPI、LangGraph、RAG、FAISS...

请仅将以上内容作为参考，不得编造用户未提供的经历。
```

---

## 8. 多文档召回方案

### 简历优化

```python
kbs = ["jd", "project_template", "skill_keyword", "interview_question"]
```

### 岗位 JD 分析

```python
kbs = ["jd", "skill_keyword", "interview_question"]
```

### 项目改写

```python
kbs = ["project_template", "skill_keyword", "interview_question"]
```

### 打招呼生成

```python
kbs = ["greeting_template", "jd"]
```

---

## 9. API

### 导入知识

```http
POST /v1/rag/index
Authorization: Bearer <shared-internal-token>
Content-Type: application/json

{
  "docs": [
    {
      "kb": "jd",
      "docId": "jd-java-1",
      "text": "Java 后端岗位要求 Spring Boot、MySQL、Redis。",
      "metadata": {"role": "java"}
    }
  ],
  "chunkSize": 500,
  "overlap": 50
}
```

### 检索

```http
POST /v1/rag/search

{
  "query": "Java Spring Boot Redis",
  "kbs": ["jd", "skill_keyword"],
  "topK": 5
}
```

### Prompt 上下文

```http
POST /v1/rag/prompt-context

{
  "query": "LangGraph RAG Agent 项目",
  "kbs": ["project_template", "interview_question"],
  "topK": 3
}
```

---

## 10. 种子数据导入

```bash
cd agent-jd-python
python scripts/import_knowledge.py --file seed/knowledge.jsonl
python scripts/rag_smoke.py
```

---

## 11. 企业级注意事项

- **Embedding 模型变更必须重建索引**:不同模型维度不同,不可混用。
- **多实例部署**:FAISS 写入建议单独 indexer 实例负责,查询实例只读。
- **元数据过滤**:可按 `role/channel/topic` 过滤召回内容。
- **召回评估**:记录 query、hit、score、最终 LLM 质量反馈,用于调参。
- **Prompt 安全**:RAG 内容作为参考上下文,不得覆盖 system 指令。
