# 04 - 存储设计 (MySQL / Redis / FAISS)

本文档对应需求中的 **8. Redis 设计 / 9. MySQL 设计思路 / 10. FAISS 设计思路**。

---

## 1. MySQL 设计思路

### 1.1 总体原则

- **库分域**:逻辑上每个领域一个 schema 段(实际单库,通过表前缀区分):`u_*` 用户、`r_*` 简历、`j_*` JD、`t_*` 任务、`g_*` 打招呼、`m_*` 匹配、`s_*` 系统。
- **主键**:全部 `BIGINT UNSIGNED` 雪花 ID,避免暴露自增。
- **逻辑删除**:`is_deleted TINYINT DEFAULT 0`,所有 SELECT 默认过滤(MyBatis-Plus 注解)。
- **公共字段**:`created_by / updated_by / created_at / updated_at / version` 五件套。
- **大文本/JSON**:Prompt 输入输出、AI 结果 → `JSON` 列;长文(> 16KB)→ MinIO,DB 存路径。
- **索引策略**:每张表必有 `(tenant_id, user_id, created_at)` 复合索引(便于按租户+用户拉历史)。
- **分区**:`ai_task` / `ai_task_event` 按月分区(RANGE on `created_at`)。
- **审计**:核心写操作走 `audit_log`(异步写)。

### 1.2 核心表 (DDL 关键字段)

#### 用户域

```sql
CREATE TABLE u_user (
  id            BIGINT UNSIGNED PRIMARY KEY,
  username      VARCHAR(64)  NOT NULL UNIQUE,
  email         VARCHAR(128) UNIQUE,
  phone         VARCHAR(32)  UNIQUE,
  password_hash VARCHAR(128) NOT NULL,         -- bcrypt
  status        TINYINT      NOT NULL DEFAULT 1,  -- 1启用 0禁用
  role          VARCHAR(32)  NOT NULL DEFAULT 'USER',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted    TINYINT      NOT NULL DEFAULT 0,
  version       INT          NOT NULL DEFAULT 0,
  KEY idx_status_created (status, created_at)
);

CREATE TABLE u_user_profile (
  user_id      BIGINT UNSIGNED PRIMARY KEY,
  nickname     VARCHAR(64),
  avatar_url   VARCHAR(255),
  job_title    VARCHAR(64),     -- 期望职位
  experience_years INT,
  city         VARCHAR(32),
  extra        JSON
);

CREATE TABLE u_user_quota (
  user_id        BIGINT UNSIGNED PRIMARY KEY,
  daily_ai_limit INT NOT NULL DEFAULT 50,
  monthly_ai_limit INT NOT NULL DEFAULT 1000,
  reset_at       DATETIME
);
```

#### 简历域

```sql
CREATE TABLE r_resume (
  id           BIGINT UNSIGNED PRIMARY KEY,
  user_id      BIGINT UNSIGNED NOT NULL,
  title        VARCHAR(128) NOT NULL,
  source       TINYINT NOT NULL,          -- 1上传 2手填 3 AI 生成
  file_url     VARCHAR(255),              -- MinIO 路径
  raw_text     MEDIUMTEXT,                -- 解析后纯文本
  status       TINYINT NOT NULL,          -- 1未解析 2已解析 3已优化
  current_version_id BIGINT UNSIGNED,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted   TINYINT NOT NULL DEFAULT 0,
  KEY idx_user_created (user_id, created_at)
);

CREATE TABLE r_resume_section (
  id          BIGINT UNSIGNED PRIMARY KEY,
  resume_id   BIGINT UNSIGNED NOT NULL,
  section     VARCHAR(32) NOT NULL,       -- basic/skill/work/project/education
  content_md  MEDIUMTEXT,
  content_json JSON,
  sort_no     INT,
  KEY idx_resume_section (resume_id, section)
);

CREATE TABLE r_resume_version (
  id          BIGINT UNSIGNED PRIMARY KEY,
  resume_id   BIGINT UNSIGNED NOT NULL,
  version_no  INT NOT NULL,
  source_task_id BIGINT UNSIGNED,         -- 由哪个 AI 任务产生
  snapshot_json JSON NOT NULL,            -- 全量快照
  diff_json   JSON,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_resume_ver (resume_id, version_no)
);
```

#### JD 域

```sql
CREATE TABLE j_jd (
  id          BIGINT UNSIGNED PRIMARY KEY,
  user_id     BIGINT UNSIGNED NOT NULL,
  title       VARCHAR(128) NOT NULL,
  company     VARCHAR(128),
  city        VARCHAR(32),
  raw_text    MEDIUMTEXT NOT NULL,
  source_url  VARCHAR(512),
  status      TINYINT NOT NULL DEFAULT 1, -- 1未解析 2已解析
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_deleted  TINYINT NOT NULL DEFAULT 0,
  KEY idx_user_created (user_id, created_at)
);

CREATE TABLE j_jd_analysis (
  id          BIGINT UNSIGNED PRIMARY KEY,
  jd_id       BIGINT UNSIGNED NOT NULL UNIQUE,
  hard_skills JSON,    -- [{name,weight}]
  soft_skills JSON,
  bonus_items JSON,
  summary     TEXT,
  prompt_version VARCHAR(32),
  model       VARCHAR(64),
  tokens      INT,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### AI 任务域(核心)

```sql
CREATE TABLE t_ai_task (
  id          BIGINT UNSIGNED PRIMARY KEY,
  task_uuid   CHAR(36) NOT NULL UNIQUE,    -- 对外暴露
  user_id     BIGINT UNSIGNED NOT NULL,
  capability  VARCHAR(32) NOT NULL,        -- resume_optimize / jd_analyze / ...
  biz_id      BIGINT UNSIGNED,             -- 业务关联 ID(resume_id / jd_id)
  status      TINYINT NOT NULL,            -- 0PENDING 1RUNNING 2SUCCESS 3FAILED 4CANCELED
  progress    TINYINT NOT NULL DEFAULT 0,  -- 0~100
  input_json  JSON,
  output_json JSON,
  error_msg   VARCHAR(512),
  prompt_version VARCHAR(32),
  model       VARCHAR(64),
  tokens_in   INT,
  tokens_out  INT,
  cost_cents  INT,                         -- 成本(分)
  trace_id    VARCHAR(64),
  started_at  DATETIME,
  finished_at DATETIME,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_user_status (user_id, status, created_at),
  KEY idx_capability (capability, created_at)
) PARTITION BY RANGE (TO_DAYS(created_at)) (
  PARTITION p202601 VALUES LESS THAN (TO_DAYS('2026-02-01')),
  PARTITION p202602 VALUES LESS THAN (TO_DAYS('2026-03-01')),
  PARTITION pmax    VALUES LESS THAN MAXVALUE
);

CREATE TABLE t_ai_task_event (
  id         BIGINT UNSIGNED PRIMARY KEY,
  task_id    BIGINT UNSIGNED NOT NULL,
  stage      VARCHAR(32),                  -- analyze_jd / rewrite / review / ...
  level      VARCHAR(16) NOT NULL,         -- INFO/WARN/ERROR
  message    TEXT,
  payload    JSON,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  KEY idx_task_time (task_id, created_at)
);
```

#### 匹配 / 打招呼 / 系统

```sql
CREATE TABLE m_match_record (
  id           BIGINT UNSIGNED PRIMARY KEY,
  user_id      BIGINT UNSIGNED NOT NULL,
  resume_id    BIGINT UNSIGNED NOT NULL,
  jd_id        BIGINT UNSIGNED NOT NULL,
  total_score  DECIMAL(5,2),
  hard_score   DECIMAL(5,2),
  soft_score   DECIMAL(5,2),
  exp_score    DECIMAL(5,2),
  gap_json     JSON,
  suggest_md   MEDIUMTEXT,
  task_id      BIGINT UNSIGNED,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_user_created (user_id, created_at),
  UNIQUE KEY uk_resume_jd (resume_id, jd_id)
);

CREATE TABLE g_greeting_template (
  id          BIGINT UNSIGNED PRIMARY KEY,
  channel     VARCHAR(32) NOT NULL,         -- boss/liepin/email
  scenario    VARCHAR(32),                  -- 投递/内推
  content_md  TEXT NOT NULL,
  is_default  TINYINT NOT NULL DEFAULT 0
);

CREATE TABLE g_greeting_record (
  id          BIGINT UNSIGNED PRIMARY KEY,
  user_id     BIGINT UNSIGNED NOT NULL,
  jd_id       BIGINT UNSIGNED,
  channel     VARCHAR(32),
  content     TEXT NOT NULL,
  task_id     BIGINT UNSIGNED,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_user (user_id, created_at)
);

CREATE TABLE s_audit_log (
  id          BIGINT UNSIGNED PRIMARY KEY,
  user_id     BIGINT UNSIGNED,
  action      VARCHAR(64) NOT NULL,
  resource    VARCHAR(64),
  resource_id BIGINT UNSIGNED,
  ip          VARCHAR(64),
  ua          VARCHAR(255),
  trace_id    VARCHAR(64),
  detail      JSON,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_user_action (user_id, action, created_at)
);

CREATE TABLE s_config (
  k VARCHAR(128) PRIMARY KEY,
  v JSON,
  remark VARCHAR(255),
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 1.3 ER 关系简图

```
u_user 1──* r_resume 1──* r_resume_section
                 1──* r_resume_version

u_user 1──* j_jd 1──1 j_jd_analysis

u_user 1──* t_ai_task ──┐
                          ├─► biz_id 指向 r_resume / j_jd / m_match_record
m_match_record (resume_id, jd_id)
g_greeting_record (jd_id)
```

---

## 2. Redis 设计

### 2.1 命名规范

`{业务前缀}:{对象}:{标识}[:子项]`,所有 Key **必须**带 TTL,除非显式说明长期。

### 2.2 Key 清单

| Key | 类型 | TTL | 用途 |
| --- | --- | --- | --- |
| `auth:access:{jti}` | String | 15min | access_token 黑名单(注销时写入) |
| `auth:refresh:{uid}` | String | 7d | refresh_token 哈希 |
| `auth:login:fail:{uid}` | String/INCR | 30min | 登录失败次数,超 5 次锁定 |
| `user:info:{uid}` | Hash | 30min | 用户基础信息缓存 (穿透 → DB) |
| `user:quota:{uid}:{yyyymmdd}` | INCR | 36h | 当日 AI 调用次数 |
| `user:quota:m:{uid}:{yyyymm}` | INCR | 35d | 当月 AI 调用次数 |
| `rl:{uid}:{api}` | Lua 令牌桶 | 滑动 1min | 用户级接口限流 |
| `lock:resume:{rid}` | Set NX | 30s | 防并发写同一简历 |
| `cache:jd_analysis:{md5}` | String JSON | 24h | JD 分析结果按文本 hash 缓存 |
| `cache:llm:{capability}:{hash}` | String JSON | 1h~24h | LLM 输入 hash → 输出缓存(节省成本) |
| `idem:{capability}:{request_id}` | SETNX | 30min | 幂等去重 |
| `ai:task:queue` | Stream | 永久 | 任务队列 |
| `ai:task:{taskId}` | Hash | 24h | 任务状态:status/progress/started_at |
| `ai:task:{taskId}:stream` | List | 24h | 流式 token 缓冲(SSE 重连时回放) |
| `ai:task:{taskId}:lock` | Set NX | 5min | Worker 抢占锁 |
| `prompt:active:{capability}` | String | 长期 | 当前生效 prompt 版本号 |
| `feature:flag:{name}` | String | 长期 | 功能开关 |
| `online:user` | ZSet | 滑动 5min | 在线用户(score=lastSeen) |

### 2.3 关键模式

**(1) 幂等**

```
SET idem:resume_optimize:{request_id} {task_id} NX EX 1800
→ 1 表示首次,正常处理
→ 0 表示重复,直接返回已存 task_id
```

**(2) 限流(令牌桶 Lua)**

```lua
-- KEYS[1]=rl:uid:api  ARGV: capacity, refillPerSec, now, cost
local tokens = tonumber(redis.call('HGET', KEYS[1], 'tokens') or ARGV[1])
local ts     = tonumber(redis.call('HGET', KEYS[1], 'ts') or ARGV[3])
local fill   = (ARGV[3] - ts) * ARGV[2]
tokens = math.min(ARGV[1], tokens + fill)
if tokens < tonumber(ARGV[4]) then return 0 end
tokens = tokens - ARGV[4]
redis.call('HMSET', KEYS[1], 'tokens', tokens, 'ts', ARGV[3])
redis.call('EXPIRE', KEYS[1], 60)
return 1
```

**(3) 任务队列**

- 生产:`XADD ai:task:queue * task_id ... capability ... user_id ...`
- 消费:`XREADGROUP GROUP worker {consumer} COUNT 10 BLOCK 1000 STREAMS ai:task:queue >`
- 死信:`XACK` 失败 N 次 → `XADD ai:task:dlq` + 告警

**(4) SSE 流式回放**

- Worker 每收到 token → `RPUSH ai:task:{id}:stream {json}`
- Java 控制器 SSE 端点订阅 + 已 push 的历史一次性下发,保证重连不丢 token。

---

## 3. FAISS 设计

### 3.1 索引规划

| Index | 维度 | 类型 | 数据量级 | 持久化路径 |
| --- | --- | --- | --- | --- |
| `resume_corpus` | 1024 (bge-m3) | `IndexFlatIP`(<10w) / `IndexHNSWFlat`(>10w) | 10w 量级 | `/data/faiss/resume.index` |
| `jd_corpus` | 1024 | 同上 | 5w 量级 | `/data/faiss/jd.index` |
| `project_corpus` | 1024 | 同上 | 20w 量级 | `/data/faiss/project.index` |
| `skill_taxonomy` | 1024 | `IndexFlatIP` | < 5k | `/data/faiss/skill.index` |

> **维度选择**:中文场景用 bge-m3(1024) 或 bge-base-zh-v1.5(768);英文兼顾用 OpenAI `text-embedding-3-small`(1536)。**生产环境固定一个 Embedding 模型,变更需要重建索引**。

### 3.2 数据模型(向量 + 元数据分离)

FAISS 只存向量,元数据另存 SQLite/JSON,通过整型 ID 关联。

```
resume.index           ← FAISS 向量
resume.meta.sqlite     ← 表 (id, doc_id, chunk_idx, text, source, tags_json, created_at)
```

```python
class FaissStore:
    def add(self, items: list[Doc]) -> list[int]:
        ids = self._next_ids(len(items))
        embeddings = self.embedder.embed([x.text for x in items])
        self.index.add_with_ids(embeddings, np.array(ids))
        self.meta.bulk_insert(items, ids)
        return ids

    def search(self, query: str, top_k=5, filters=None):
        q = self.embedder.embed([query])
        D, I = self.index.search(q, top_k * 4)         # 多召回 4 倍
        rows = self.meta.fetch(I[0].tolist())
        rows = [r for r in rows if self._match(r, filters)][:top_k]
        return list(zip(rows, D[0]))
```

### 3.3 切分与入库流程

```
原文 ──► clean (去 HTML / 表情 / 多空格)
       ──► splitter (Recursive 500/50,中文按句号优先)
       ──► dedup (simhash 去重)
       ──► embedder (批量 64 条/次)
       ──► faiss.add_with_ids
       ──► meta.bulk_insert
       ──► persist (每 5 分钟或满 1000 条 dump 一次)
```

### 3.4 增量、重建、备份

- **增量**:在线 `add`,周期性 `write_index` 落盘。
- **重建**:Embedding 模型升级时,启 `reindex_job` 全量重算 → 写到 `*.next.index` → 原子 rename。
- **备份**:每天凌晨 cp `*.index` 到对象存储,保留 7 天。
- **多副本**:Python 服务多实例时,索引放共享卷(NFS/CFS)+ 只读模式;写入由专用 indexer 实例负责,通过 inotify 重载。

### 3.5 检索质量优化

- **混合检索**:FAISS 向量 + BM25 关键词,加权:`score = 0.7 * vec + 0.3 * bm25`。
- **MMR**:输出前用 MMR 重排,提高多样性,避免 top_k 全是相似片段。
- **元数据过滤**:`filters={"role": "Java", "exp_years": ">=3"}`,先粗排再精排。
- **查询改写**:用户问题先经 `query_rewrite` chain → 抽取关键技能词 → 增强检索召回。

---

## 4. 三类存储职责边界(避免越权)

| 数据 | 落地位置 | 不要放在 |
| --- | --- | --- |
| 用户、资料、配额、任务元信息 | **MySQL** | Redis(只能缓存) |
| Token 黑名单、限流、队列、热点缓存 | **Redis** | MySQL(写放大) |
| 文本向量、相似度检索 | **FAISS** | MySQL(没有向量索引) |
| 大文件(PDF/DOCX 原件) | **MinIO** | MySQL BLOB |
| 长文本输入输出快照 | **MinIO + DB 存路径** 或 DB JSON(<1MB) | 全部塞 DB |

