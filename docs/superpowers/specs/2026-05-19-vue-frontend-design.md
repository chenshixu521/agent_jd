# Vue3 前端设计 - AI 求职 Agent 平台

## 1. 目标

为《基于 Spring Boot + LangGraph 的 AI 求职 Agent 平台》实现一个可运行的企业级前端工程。

技术栈：

- Vue3
- Vite
- TypeScript
- Element Plus
- Pinia
- Axios
- markdown-it
- lucide-vue-next

前端采用“企业控制台 + AI 工作台混合型”设计：左侧导航承载业务模块，首页提供 AI 工作台入口，各页面独立完成简历、JD、AI 分析、项目改写、匹配度报告和多轮聊天。

---

## 2. API 对接策略

采用“双模式”：

1. 默认对接真实 Java 后端 `/api/*`。
2. 开发阶段提供 mock fallback，避免后端或数据库未启动时页面不可用。
3. Axios 统一封装 token、错误处理和响应解包。

真实后端关键接口：

| 模块 | 接口 |
| --- | --- |
| 登录 | `POST /api/auth/login` |
| 注册 | `POST /api/auth/register` |
| 当前用户 | `GET /api/auth/me` |
| 文件上传 | `POST /api/files/upload` |
| 简历 | `/api/resumes` |
| JD | `/api/jds` |
| AI 任务 | `/api/tasks` |
| 对话历史 | `/api/conversations` |

AI 能力通过 Java `/api/tasks` 调用 Python Agent。

---

## 3. 工程结构

```text
agent-jd-web/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── .env.development
├── .env.production
└── src/
    ├── main.ts
    ├── App.vue
    ├── router/index.ts
    ├── stores/
    │   ├── auth.ts
    │   ├── task.ts
    │   ├── resume.ts
    │   ├── jd.ts
    │   └── chat.ts
    ├── api/
    │   ├── http.ts
    │   ├── mock.ts
    │   ├── auth.ts
    │   ├── file.ts
    │   ├── resume.ts
    │   ├── jd.ts
    │   ├── task.ts
    │   └── conversation.ts
    ├── layouts/MainLayout.vue
    ├── components/
    │   ├── layout/AppSidebar.vue
    │   ├── layout/AppHeader.vue
    │   ├── chat/ChatWindow.vue
    │   ├── chat/ChatMessage.vue
    │   ├── chat/ChatInput.vue
    │   ├── common/MarkdownView.vue
    │   ├── common/TaskStatusTag.vue
    │   ├── common/UploadCard.vue
    │   └── match/MatchScoreCard.vue
    ├── views/
    │   ├── auth/Login.vue
    │   ├── auth/Register.vue
    │   ├── dashboard/Dashboard.vue
    │   ├── resume/ResumeUpload.vue
    │   ├── jd/JdUpload.vue
    │   ├── analysis/AiAnalysis.vue
    │   ├── rewrite/ProjectRewrite.vue
    │   ├── match/MatchReport.vue
    │   └── chat/AgentChat.vue
    ├── types/api.ts
    ├── types/domain.ts
    ├── utils/token.ts
    ├── utils/markdown.ts
    ├── utils/format.ts
    └── styles/index.scss
```

---

## 4. 路由设计

| Path | 页面 | 鉴权 |
| --- | --- | --- |
| `/login` | 登录 | 否 |
| `/register` | 注册 | 否 |
| `/` | 首页工作台 | 是 |
| `/resume` | 简历上传/管理 | 是 |
| `/jd` | JD 上传/管理 | 是 |
| `/analysis` | AI 分析 | 是 |
| `/rewrite` | AI 项目改写 | 是 |
| `/match` | 匹配度展示 | 是 |
| `/chat` | Agent 对话 | 是 |

路由守卫：

- 无 token 访问私有页面时跳转 `/login`。
- 登录成功后跳转 `/`。
- token 存储在 localStorage，由 Pinia 初始化恢复。

---

## 5. 页面功能

### 登录/注册

- Element Plus 表单校验。
- 登录成功保存 token 和用户信息。
- 支持 mock fallback 登录。

### 首页

- 展示简历数量、JD 数量、AI 任务数量、最近任务。
- 快捷入口：上传简历、录入 JD、发起分析、打开对话。

### 简历上传

- 文件上传到 `/api/files/upload`。
- 上传成功后创建简历 `/api/resumes`。
- 支持手动粘贴简历文本。

### JD 上传

- 输入 title/company/city/rawText/sourceUrl。
- 保存到 `/api/jds`。
- 可触发 `jd/analyze` 任务。

### AI 分析

- 选择简历和 JD。
- 提交 `/api/tasks`：`capability=resume`、`action=optimize`。
- Markdown 渲染 AI 返回结果。
- 展示任务状态。

### 项目改写

- 输入项目文本和 JD。
- 提交 `/api/tasks`：`capability=project`、`action=rewrite`。
- Markdown 展示改写结果。

### 匹配度展示

- 提交 `/api/tasks`：`capability=match`、`action=analyze`。
- 展示总分、硬技能、软技能、经验匹配、缺失技能、建议。

### 对话页面/聊天窗口

- 支持多轮消息。
- 渲染 Markdown。
- 保留 sessionId。
- 提交 `/api/tasks`：`capability=chat`、`action=message`。

---

## 6. 状态管理

Pinia Store：

| Store | 责任 |
| --- | --- |
| `auth` | token、用户、登录、注册、退出 |
| `resume` | 简历列表、当前简历、创建简历 |
| `jd` | JD 列表、当前 JD、创建 JD |
| `task` | AI 任务提交、任务列表、任务结果 |
| `chat` | sessionId、消息列表、发送消息 |

---

## 7. 错误处理

Axios 拦截器统一处理：

- 自动附加 `Authorization: Bearer {token}`。
- `401` 或业务 code `40101/40102` 时清理 token 并跳转登录。
- 业务失败时用 Element Plus `ElMessage.error` 提示。
- 如果启用 mock fallback，请求失败时返回 mock 数据。

---

## 8. Markdown 渲染

使用 `markdown-it`：

- AI 输出统一通过 `MarkdownView` 组件渲染。
- 用 CSS 限制代码块、表格、列表样式。
- 默认不启用 HTML，避免 XSS。

---

## 9. 视觉风格

设计关键词：

- 现代 SaaS
- 企业控制台
- AI 工作台
- 卡片式分析
- 蓝紫渐变点缀

颜色：

```text
Primary: #2563eb
AI Accent: #7c3aed
Success: #10b981
Warning: #f59e0b
Danger: #ef4444
Background: #f8fafc
Card: #ffffff
Text: #0f172a
Muted: #64748b
```

---

## 10. 测试与验证

前端开发完成后验证：

1. `npm install`
2. `npm run build`
3. `npm run dev`
4. 登录页可访问。
5. mock fallback 下各页面可展示。
6. Java 后端启动后可真实登录、上传、提交 AI 任务。

---

## 11. 明确不做

本阶段不实现：

- SSE 流式输出。
- 复杂权限 RBAC 菜单。
- 图表库深度可视化。
- 在线简历编辑器。
- 前端单元测试体系。

这些可在 v2 增量实现。
