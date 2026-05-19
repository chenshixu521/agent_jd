# agent-jd-java

Spring Boot 后端服务,实现 AI 求职 Agent 平台的 Java 主业务层。

## 技术栈

- Java 17
- Spring Boot 3.3
- Spring MVC
- MyBatis-Plus
- MySQL 8
- Redis 7
- JWT (jjwt)
- WebClient 调用 Python Agent 服务

## 已实现模块

| 模块 | API 前缀 | 说明 |
| --- | --- | --- |
| 用户认证 | `/api/auth` | 注册、登录、当前用户 |
| 文件上传 | `/api/files` | 本地上传、下载、元数据查询 |
| 简历管理 | `/api/resumes` | 创建、列表、详情、更新、删除 |
| 岗位 JD | `/api/jds` | 创建、列表、详情、更新、删除 |
| AI 任务 | `/api/tasks` | 提交 Agent 任务、状态与结果查询 |
| 对话历史 | `/api/conversations` | 对话与消息管理 |

## 启动前准备

1. 创建 MySQL 表:

```bash
mysql -u<MYSQL_USER> -p<MYSQL_PASSWORD> < ../deploy/sql/java-backend-init.sql
```

2. 启动 Redis。

3. 设置环境变量或使用默认值:

```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=agent_jd
MYSQL_USER=root
MYSQL_PASSWORD=<your-mysql-password>
REDIS_HOST=localhost
REDIS_PORT=6379
JWT_SECRET=<at-least-32-byte-secret>
AGENT_BASE_URL=http://localhost:8000
AGENT_INTERNAL_TOKEN=<shared-internal-token>
```

## 本地运行

```bash
mvn spring-boot:run
```

## Python Agent 调用契约

AI 任务提交接口会调用:

```http
POST {AGENT_BASE_URL}/v1/{capability}/{action}
Authorization: Bearer {AGENT_INTERNAL_TOKEN}
X-Trace-Id: {traceId}
X-User-Id: {userId}

{
  "taskId": "uuid",
  "stream": false,
  "payload": {}
}
```

Python 返回:

```json
{
  "code": 0,
  "msg": "ok",
  "data": {}
}
```
