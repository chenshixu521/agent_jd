# 09 - Redis 会话上下文管理模块

本文档说明《基于大模型的简历与岗位匹配 Agent 系统》中的 Redis 会话上下文设计。

---

## 1. Redis 结构设计

| Key | 类型 | TTL | 用途 |
| --- | --- | --- | --- |
| `session:state:{sessionId}` | String(JSON) | 7d | 会话状态、标题、用户、摘要、轮次 |
| `session:messages:{sessionId}` | List(JSON) | 7d | 历史消息,按时间追加 |
| `session:user:{userId}` | ZSet | 7d | 用户会话列表,score 为更新时间 |
| `agent:task:{taskId}` | String(JSON) | 24h | Agent 任务状态、进度、错误 |
| `agent:context:{taskId}` | String(JSON) | 24h | Agent 请求与结果上下文 |
| `agent:event:{taskId}` | List(JSON) | 24h | LangGraph 节点事件 |
| `prompt:ctx:{capability}:{version}:{hash}` | String(JSON) | 1h | Prompt 上下文/LLM 结果缓存 |

---

## 2. Session 设计

```json
{
  "session_id": "uuid",
  "user_id": "1001",
  "title": "求职 Agent 对话",
  "status": "ACTIVE",
  "summary": "",
  "turn_count": 3,
  "created_at": "2026-05-19T02:00:00Z",
  "updated_at": "2026-05-19T02:10:00Z",
  "metadata": {}
}
```

状态：

| 状态 | 含义 |
| --- | --- |
| `ACTIVE` | 正常对话中 |
| `ARCHIVED` | 已归档 |
| `DELETED` | 已删除 |

---

## 3. 历史消息存储

```json
{
  "message_id": "uuid",
  "role": "user",
  "content": "请帮我分析这个 JD",
  "created_at": "2026-05-19T02:00:00Z",
  "metadata": {
    "task_id": "task-uuid"
  }
}
```

写入策略：

- `RPUSH session:messages:{sessionId} {message}`
- `LTRIM session:messages:{sessionId} -200 -1`
- `EXPIRE session:messages:{sessionId} 7d`

---

## 4. 上下文缓存代码

实现文件：

```text
agent-jd-python/app/memory/session_store.py
```

核心能力：

- `create_session`
- `save_session`
- `get_session`
- `append_message`
- `list_messages`
- `build_context`
- `set_task_status`
- `get_task_status`
- `get_prompt_cache`
- `set_prompt_cache`

---

## 5. 会话管理 API

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/v1/sessions` | 创建会话 |
| `GET` | `/v1/sessions/{sessionId}` | 获取会话状态 |
| `POST` | `/v1/sessions/{sessionId}/messages` | 追加消息 |
| `GET` | `/v1/sessions/{sessionId}/messages` | 获取历史消息 |
| `GET` | `/v1/sessions/{sessionId}/context` | 获取裁剪后的上下文 |

---

## 6. 多轮对话流程

```text
用户消息
  │
  ▼
chat_node
  │
  ├── 获取/创建 session
  ├── 读取 session:messages:{sessionId}
  ├── ContextWindowPolicy 裁剪上下文
  ├── PromptRegistry 渲染 prompt
  ├── 查询 prompt:ctx 缓存
  ├── LLM 生成回复
  ├── 写入 user/assistant 消息
  └── 返回 session_id + answer
```

---

## 7. Token 限制方案

默认策略：

```python
ContextWindowPolicy(max_tokens=4000, reserve_tokens=800, max_messages=30)
```

含义：

- `max_tokens`: 模型上下文预算
- `reserve_tokens`: 为模型输出预留预算
- `max_messages`: 最多参与裁剪的最近消息数

Token 估算：

- 英文按空格词数估算
- 中文按 CJK 字符估算
- fallback 使用非空字符数 / 4

---

## 8. 上下文裁剪方案

裁剪规则：

1. 从最近消息开始向前选择。
2. 累计 token 不超过 `max_tokens - reserve_tokens`。
3. 保留最新一条消息；如果单条过长,截取尾部内容。
4. 最多保留 `max_messages` 条消息。

优点：

- 保证最近上下文优先。
- 避免 prompt 超长。
- 对中文和英文均可用。
- 不依赖 tokenizer,本地可运行。

后续可升级：

- 使用模型 tokenizer 精确计数。
- 对被裁剪的早期消息做摘要,写入 `session:state.summary`。
- 按消息重要度加权保留。

---

## 9. Prompt 上下文缓存

缓存 Key：

```text
prompt:ctx:{capability}:{version}:{sha256(payload)}
```

示例：

```text
prompt:ctx:chat:v1:9fbd7e...
```

用途：

- 相同会话上下文和问题命中缓存。
- 降低 LLM 成本。
- 减少重复等待。

---

## 10. 与已有 Agent 状态关系

| 模块 | Redis Key | 说明 |
| --- | --- | --- |
| 会话上下文 | `session:*` | 多轮对话长期上下文 |
| Agent 任务 | `agent:task:*` | 单次任务执行状态 |
| LangGraph 事件 | `agent:event:*` | 节点级事件追踪 |
| Prompt 缓存 | `prompt:ctx:*` | Prompt/LLM 结果缓存 |
