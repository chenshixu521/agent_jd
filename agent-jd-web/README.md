# agent-jd-web

Vue3 + Element Plus 前端工程，用于 AI 求职 Agent 平台。

## 技术栈

- Vue3
- Vite
- TypeScript
- Element Plus
- Pinia
- Vue Router
- Axios
- markdown-it
- lucide-vue-next

## 页面

| 路由 | 功能 |
| --- | --- |
| `/login` | 登录 |
| `/register` | 注册 |
| `/` | 首页工作台 |
| `/resume` | 简历上传 |
| `/jd` | JD 上传 |
| `/analysis` | AI 分析 |
| `/rewrite` | AI 项目改写 |
| `/match` | 匹配度展示 |
| `/chat` | Agent 对话 |

## API 配置

前端只调用真实后端 API：

```env
VITE_API_BASE_URL=http://localhost:8080
```

## 启动

```bash
npm install
npm run dev
```

## 构建

```bash
npm run build
```

## 目录结构

```text
src/
├── api/          # Axios 和接口封装
├── components/   # 通用组件、聊天组件、布局组件
├── layouts/      # 主布局
├── router/       # Vue Router
├── stores/       # Pinia
├── styles/       # 全局样式
├── types/        # 类型定义
├── utils/        # token、markdown、format
└── views/        # 页面
```
