# Vue3 Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable Vue3 + Element Plus frontend for the AI Job Agent platform.

**Architecture:** Single Vite Vue3 app under `agent-jd-web`, using route-level pages, Pinia stores, Axios API modules, and reusable UI components. The frontend defaults to real Java backend APIs and uses mock fallback for development resilience.

**Tech Stack:** Vue3, Vite, TypeScript, Element Plus, Pinia, Vue Router, Axios, markdown-it, lucide-vue-next.

---

## File Structure

- `agent-jd-web/package.json`: dependencies and scripts.
- `agent-jd-web/vite.config.ts`: Vite config and dev proxy.
- `agent-jd-web/tsconfig.json`: TypeScript config.
- `agent-jd-web/index.html`: Vite entry.
- `agent-jd-web/.env.development`: API base URL and mock fallback flag.
- `agent-jd-web/src/main.ts`: Vue bootstrap.
- `agent-jd-web/src/App.vue`: root app.
- `agent-jd-web/src/router/index.ts`: routes and auth guard.
- `agent-jd-web/src/api/*`: Axios and backend API wrappers.
- `agent-jd-web/src/stores/*`: Pinia auth/task/resume/jd/chat state.
- `agent-jd-web/src/layouts/MainLayout.vue`: shell layout.
- `agent-jd-web/src/components/*`: layout, chat, markdown, upload, task, match components.
- `agent-jd-web/src/views/*`: page-level views.
- `agent-jd-web/src/styles/index.scss`: global theme.

---

### Task 1: Scaffold Vite Vue project

**Files:**
- Create: `agent-jd-web/package.json`
- Create: `agent-jd-web/vite.config.ts`
- Create: `agent-jd-web/tsconfig.json`
- Create: `agent-jd-web/index.html`
- Create: `agent-jd-web/.env.development`
- Create: `agent-jd-web/.env.production`

- [ ] Create project config files.
- [ ] Verify `npm install` can resolve dependencies.

### Task 2: Core app bootstrap

**Files:**
- Create: `agent-jd-web/src/main.ts`
- Create: `agent-jd-web/src/App.vue`
- Create: `agent-jd-web/src/styles/index.scss`
- Create: `agent-jd-web/src/types/api.ts`
- Create: `agent-jd-web/src/types/domain.ts`
- Create: `agent-jd-web/src/utils/token.ts`
- Create: `agent-jd-web/src/utils/format.ts`
- Create: `agent-jd-web/src/utils/markdown.ts`

- [ ] Implement Vue app bootstrap with Element Plus, Pinia, router.
- [ ] Implement global styles and utility modules.

### Task 3: API layer and mock fallback

**Files:**
- Create: `agent-jd-web/src/api/http.ts`
- Create: `agent-jd-web/src/api/mock.ts`
- Create: `agent-jd-web/src/api/auth.ts`
- Create: `agent-jd-web/src/api/file.ts`
- Create: `agent-jd-web/src/api/resume.ts`
- Create: `agent-jd-web/src/api/jd.ts`
- Create: `agent-jd-web/src/api/task.ts`
- Create: `agent-jd-web/src/api/conversation.ts`

- [ ] Implement Axios instance with token injection and response unwrap.
- [ ] Implement mock fallback helpers.
- [ ] Implement API modules matching Java backend.

### Task 4: Pinia stores and routing

**Files:**
- Create: `agent-jd-web/src/router/index.ts`
- Create: `agent-jd-web/src/stores/auth.ts`
- Create: `agent-jd-web/src/stores/resume.ts`
- Create: `agent-jd-web/src/stores/jd.ts`
- Create: `agent-jd-web/src/stores/task.ts`
- Create: `agent-jd-web/src/stores/chat.ts`

- [ ] Implement auth store with login/register/logout/bootstrap.
- [ ] Implement domain stores for resume, JD, task, chat.
- [ ] Implement route guard requiring token for app pages.

### Task 5: Layout and common components

**Files:**
- Create: `agent-jd-web/src/layouts/MainLayout.vue`
- Create: `agent-jd-web/src/components/layout/AppSidebar.vue`
- Create: `agent-jd-web/src/components/layout/AppHeader.vue`
- Create: `agent-jd-web/src/components/common/MarkdownView.vue`
- Create: `agent-jd-web/src/components/common/TaskStatusTag.vue`
- Create: `agent-jd-web/src/components/common/UploadCard.vue`
- Create: `agent-jd-web/src/components/match/MatchScoreCard.vue`

- [ ] Implement enterprise console shell.
- [ ] Implement reusable Markdown, upload, task status, match score components.

### Task 6: Chat components

**Files:**
- Create: `agent-jd-web/src/components/chat/ChatWindow.vue`
- Create: `agent-jd-web/src/components/chat/ChatMessage.vue`
- Create: `agent-jd-web/src/components/chat/ChatInput.vue`

- [ ] Implement chat UI with Markdown assistant output.
- [ ] Implement send-on-enter and loading state.

### Task 7: Page views

**Files:**
- Create: `agent-jd-web/src/views/auth/Login.vue`
- Create: `agent-jd-web/src/views/auth/Register.vue`
- Create: `agent-jd-web/src/views/dashboard/Dashboard.vue`
- Create: `agent-jd-web/src/views/resume/ResumeUpload.vue`
- Create: `agent-jd-web/src/views/jd/JdUpload.vue`
- Create: `agent-jd-web/src/views/analysis/AiAnalysis.vue`
- Create: `agent-jd-web/src/views/rewrite/ProjectRewrite.vue`
- Create: `agent-jd-web/src/views/match/MatchReport.vue`
- Create: `agent-jd-web/src/views/chat/AgentChat.vue`

- [ ] Implement auth pages.
- [ ] Implement dashboard and business pages.
- [ ] Implement AI task result rendering with Markdown.

### Task 8: Verification

**Files:**
- Modify as needed based on build output.

- [ ] Run `npm install` in `agent-jd-web`.
- [ ] Run `npm run build`.
- [ ] Fix TypeScript or Vue compile errors.
- [ ] Optionally run `npm run dev` and preview.

---

## Self Review

Spec coverage:

- Vue3 structure: Task 1-2.
- API wrapper: Task 3.
- Pages: Task 7.
- Routing: Task 4.
- Pinia: Task 4.
- Chat UI: Task 6 and Task 7.
- Markdown: Task 2 and Task 5.
- Upload: Task 3, Task 5, Task 7.
- Token management: Task 2-4.
- Modern UI: Task 5-7.

No placeholders remain. Scope is a single frontend app v1 and excludes SSE/RBAC as specified in the design.
