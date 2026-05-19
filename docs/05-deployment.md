# 05 - 工程化与 Docker 部署架构

本文档对应需求中的 **12. 工程化设计 / 13. Docker 部署架构**。

---

## 1. 工程化总览

| 维度 | 方案 |
| --- | --- |
| **代码管理** | Monorepo,顶层目录:`agent-jd-java / agent-jd-python / agent-jd-web / deploy / docs` |
| **分支策略** | `main`(生产) / `release/*`(预发) / `develop`(集成) / `feature/*` / `hotfix/*` |
| **提交规范** | Conventional Commits + commitlint;`feat / fix / chore / docs / refactor / test / perf` |
| **代码风格** | Java: Checkstyle + Spotless;Python: ruff + black + mypy;前端: ESLint + Prettier |
| **依赖管理** | Java: Maven BOM 统一版本;Python: `pyproject.toml` + `uv` / `pip-tools` 锁版本;前端: pnpm + workspace |
| **配置管理** | 12-Factor;`.env` + Spring Profile + pydantic-settings;敏感配置走 K8s Secret / Vault |
| **国际化** | i18n 字典在前端 + Java(`messages_zh.properties`),Python 错误码与文案分离 |
| **测试** | Java:JUnit5 + Mockito + Testcontainers;Python:pytest + pytest-asyncio + httpx;前端:Vitest |
| **API 契约** | OpenAPI 3.0;Java(Knife4j)+ Python(FastAPI 自带)合并到一个 portal |
| **可观测** | 日志 JSON → Loki / ELK;指标 Prometheus + Grafana;链路 OpenTelemetry → Jaeger |
| **安全** | 依赖扫描(Trivy / Snyk);Secret 扫描(gitleaks);镜像签名(cosign,可选) |

---

## 2. CI/CD 流水线 (GitHub Actions / GitLab CI)

```
push / PR
   │
   ├── lint & unit-test           (3 个目标并行)
   │      ├─ java: mvn -T 1C verify
   │      ├─ python: ruff + pytest
   │      └─ web:    pnpm lint + vitest
   │
   ├── build images (打 tag = git sha)
   │      ├─ ghcr.io/agent-jd/java:{sha}
   │      ├─ ghcr.io/agent-jd/python:{sha}
   │      └─ ghcr.io/agent-jd/web:{sha}
   │
   ├── security scan (trivy + gitleaks)
   │
   ├── push to registry
   │
   └── deploy
          ├─ dev    自动 (合并到 develop)
          ├─ stage  手动审批 (合并到 release/*)
          └─ prod   手动审批 + 灰度 (合并到 main)
```

关键 Job 示例(GitHub Actions):

```yaml
# .github/workflows/ci.yml
name: ci
on: [push, pull_request]
jobs:
  java:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: 'temurin', java-version: '17', cache: 'maven' }
      - run: ./mvnw -B -T 1C verify
        working-directory: agent-jd-java
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements-dev.txt
      - run: ruff check . && pytest -q
        working-directory: agent-jd-python
  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with: { version: 9 }
      - run: pnpm install --frozen-lockfile && pnpm lint && pnpm test
        working-directory: agent-jd-web
```

---

## 3. Docker 部署架构

### 3.1 容器拓扑

```
┌────────────────────────────────────────────────────────────────┐
│                          docker network: agent-net             │
│                                                                │
│  ┌──────────┐   ┌─────────┐   ┌─────────┐   ┌────────────┐   │
│  │  nginx   │──►│   web   │   │  java   │──►│   python   │   │
│  │  :80/443 │   │ (静态)  │   │  :8080  │   │   :8000    │   │
│  └────┬─────┘   └─────────┘   └────┬────┘   └─────┬──────┘   │
│       │                            │              │           │
│       └─────────► java :8080  ◄────┘              │           │
│                                                   │           │
│                  ┌──────────┬───────────┬─────────┴────┐      │
│                  ▼          ▼           ▼              ▼      │
│             ┌────────┐ ┌────────┐ ┌─────────┐  ┌──────────┐  │
│             │ mysql  │ │ redis  │ │  minio  │  │  faiss   │  │
│             │ :3306  │ │ :6379  │ │ :9000   │  │ (vol)    │  │
│             └────────┘ └────────┘ └─────────┘  └──────────┘  │
└────────────────────────────────────────────────────────────────┘

Volumes:
  - mysql_data        (持久化)
  - redis_data        (持久化)
  - minio_data        (持久化)
  - faiss_data        (持久化, mount 到 python:/data/faiss)
  - nginx_logs
```

### 3.2 容器清单

| 容器 | 镜像 | 端口 | 健康检查 |
| --- | --- | --- | --- |
| `nginx` | `nginx:1.27-alpine` | 80/443 | `wget -qO- http://localhost/health` |
| `web` | 自建(多阶段 → nginx 静态) | (内) | 同上 |
| `java` | 自建(eclipse-temurin:17-jre) | 8080 | `/actuator/health` |
| `worker` | 同 java(`SPRING_PROFILES_ACTIVE=worker`) | - | `/actuator/health` |
| `python` | 自建(python:3.11-slim) | 8000 | `/v1/health` |
| `mysql` | `mysql:8.0` | 3306 | `mysqladmin ping` |
| `redis` | `redis:7-alpine` | 6379 | `redis-cli ping` |
| `minio` | `minio/minio:latest` | 9000/9001 | `/minio/health/live` |

### 3.3 Dockerfile 示例

#### Java(多阶段)

```dockerfile
# deploy/docker/java.Dockerfile
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY agent-jd-java /src
RUN mvn -B -T 1C -DskipTests package -pl agent-jd-admin -am

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /src/agent-jd-admin/target/*.jar /app/app.jar
ENV JAVA_OPTS="-XX:MaxRAMPercentage=75 -XX:+UseG1GC -Dfile.encoding=UTF-8"
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=30s \
  CMD wget -qO- http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["sh","-c","java $JAVA_OPTS -jar /app/app.jar"]
```

#### Python

```dockerfile
# deploy/docker/python.Dockerfile
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgomp1 curl && rm -rf /var/lib/apt/lists/*

COPY agent-jd-python/requirements.txt .
RUN pip install -r requirements.txt

COPY agent-jd-python /app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=30s \
  CMD curl -fs http://localhost:8000/v1/health || exit 1
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","2"]
```

#### Web(多阶段 → Nginx 静态)

```dockerfile
# deploy/docker/web.Dockerfile
FROM node:20-alpine AS build
WORKDIR /src
RUN corepack enable
COPY agent-jd-web /src
RUN pnpm install --frozen-lockfile && pnpm build

FROM nginx:1.27-alpine
COPY --from=build /src/dist /usr/share/nginx/html
COPY deploy/nginx/web.conf /etc/nginx/conf.d/default.conf
```

### 3.4 docker-compose 编排

```yaml
# deploy/docker-compose/all.yml
version: "3.9"
name: agent-jd

x-env: &env
  TZ: Asia/Shanghai

networks:
  agent-net: {}

volumes:
  mysql_data:
  redis_data:
  minio_data:
  faiss_data:

services:
  mysql:
    image: mysql:8.0
    environment:
      <<: *env
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PWD}
      MYSQL_DATABASE: agent_jd
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PWD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ../sql/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks: [agent-net]
    healthcheck:
      test: ["CMD","mysqladmin","ping","-uroot","-p${MYSQL_ROOT_PWD}"]
      interval: 10s
      retries: 10

  redis:
    image: redis:7-alpine
    command: ["redis-server","--requirepass","${REDIS_PWD}","--appendonly","yes"]
    volumes: [redis_data:/data]
    networks: [agent-net]

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_AK}
      MINIO_ROOT_PASSWORD: ${MINIO_SK}
    volumes: [minio_data:/data]
    ports: ["9001:9001"]
    networks: [agent-net]

  python:
    build:
      context: ../..
      dockerfile: deploy/docker/python.Dockerfile
    environment:
      <<: *env
      LLM_DEFAULT: ${LLM_DEFAULT}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      DASHSCOPE_API_KEY: ${DASHSCOPE_API_KEY}
      REDIS_URL: redis://:${REDIS_PWD}@redis:6379/0
      INTERNAL_SECRET: ${AGENT_SECRET}
      FAISS_DIR: /data/faiss
    volumes:
      - faiss_data:/data/faiss
    depends_on: [redis]
    networks: [agent-net]

  java:
    build:
      context: ../..
      dockerfile: deploy/docker/java.Dockerfile
    environment:
      <<: *env
      SPRING_PROFILES_ACTIVE: prod
      MYSQL_HOST: mysql
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PWD: ${MYSQL_PWD}
      REDIS_HOST: redis
      REDIS_PWD: ${REDIS_PWD}
      AGENT_BASE_URL: http://python:8000
      AGENT_SECRET: ${AGENT_SECRET}
      MINIO_ENDPOINT: http://minio:9000
      MINIO_AK: ${MINIO_AK}
      MINIO_SK: ${MINIO_SK}
      JWT_SECRET: ${JWT_SECRET}
    depends_on: [mysql, redis, minio, python]
    networks: [agent-net]

  worker:
    build:
      context: ../..
      dockerfile: deploy/docker/java.Dockerfile
    environment:
      <<: *env
      SPRING_PROFILES_ACTIVE: worker,prod
      MYSQL_HOST: mysql
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PWD: ${MYSQL_PWD}
      REDIS_HOST: redis
      REDIS_PWD: ${REDIS_PWD}
      AGENT_BASE_URL: http://python:8000
      AGENT_SECRET: ${AGENT_SECRET}
    depends_on: [java]
    networks: [agent-net]
    deploy:
      replicas: 2

  web:
    build:
      context: ../..
      dockerfile: deploy/docker/web.Dockerfile
    networks: [agent-net]

  nginx:
    image: nginx:1.27-alpine
    ports: ["80:80","443:443"]
    volumes:
      - ../nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ../nginx/conf.d:/etc/nginx/conf.d:ro
    depends_on: [java, web]
    networks: [agent-net]
```

### 3.5 Nginx 网关配置(关键片段)

```nginx
# deploy/nginx/conf.d/agent-jd.conf
upstream java_backend  { server java:8080; keepalive 32; }
upstream web_static    { server web:80; }

limit_req_zone $binary_remote_addr zone=api_ip:10m rate=20r/s;

server {
    listen 80;
    server_name _;

    location /api/ {
        limit_req zone=api_ip burst=40 nodelay;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Trace-Id $request_id;
        proxy_read_timeout 300s;        # SSE 长连接
        proxy_buffering off;            # SSE 必须关
        proxy_pass http://java_backend;
    }

    location / {
        proxy_pass http://web_static;
    }

    location = /health { return 200 'ok'; }
}
```

---

## 4. 生产环境演进(K8s 视角)

> 容器编排上 K8s 时,Compose 中的 service 一一对应:

| Compose service | K8s 资源 |
| --- | --- |
| `java` | Deployment + Service + HPA(基于 CPU/qps)+ Ingress |
| `worker` | Deployment(无 Service)+ HPA(基于 Stream lag 自定义指标)|
| `python` | Deployment + Service + HPA(并发请求数)+ PVC(faiss) |
| `web` | Deployment + Service + Ingress(静态) |
| `mysql` | StatefulSet(开发) → 生产建议 RDS |
| `redis` | StatefulSet(开发) → 生产建议云 Redis 集群 |
| `minio` | StatefulSet(开发) → 生产建议对象存储 OSS/S3 |

补充:
- ConfigMap 管理 `application.yml` 非敏感字段;Secret 管理 LLM key、JWT secret、DB 密码。
- HPA 自定义指标:Worker 基于 `XLEN ai:task:queue`,Python 基于 `inflight_request`。

---

## 5. 工程化规范要点(Checklist)

- [ ] 所有服务接入统一 `/health` 探针
- [ ] 启动失败 fail-fast,不允许"半启动"状态
- [ ] 所有外部调用必须有 timeout(永不允许默认无限等待)
- [ ] 所有 LLM 调用必须有重试 + 熔断 + 降级
- [ ] 所有日志带 `traceId / userId`,禁止打印 prompt 中的敏感字段(身份证/手机号脱敏)
- [ ] 所有数据库写操作走事务 / 幂等键
- [ ] 所有镜像非 root 用户运行
- [ ] CI 必须通过 lint + 单测才能 merge
- [ ] DB 变更走 Flyway / Liquibase,版本化
- [ ] Prompt 变更走 PR review,有版本号

