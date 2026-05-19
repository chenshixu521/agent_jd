# Java Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable Spring Boot backend for the AI 求职 Agent 平台 covering auth, file upload, resume/JD management, AI task submission/result query, conversation history, Redis, MySQL, JWT, and Python Agent invocation.

**Architecture:** Implement a single Maven module under `agent-jd-java` for the first runnable version. Keep packages separated by responsibility so it can later be split into the multi-module architecture described in `docs/02-java-backend.md`.

**Tech Stack:** Java 17, Spring Boot 3, Spring MVC, MyBatis-Plus, MySQL, Redis, JWT, WebClient, Maven.

---

### Task 1: Maven and test baseline

**Files:**
- Create: `agent-jd-java/pom.xml`
- Create: `agent-jd-java/src/test/java/com/agentjd/security/JwtUtilTest.java`

- [ ] Write a JWT unit test that creates a token and parses user id from it.
- [ ] Run `mvn -q test` in `agent-jd-java`; expected failure before `JwtUtil` exists.
- [ ] Add Maven dependencies for Spring Boot, MyBatis-Plus, MySQL, Redis, validation, JWT, WebClient, and tests.

### Task 2: Common infrastructure

**Files:**
- Create common response, exception, trace, and context classes under `com.agentjd.common`.
- Create global exception handler under `com.agentjd.web`.
- Create application entry under `com.agentjd.AgentJdApplication`.

- [ ] Implement `ApiResponse<T>` with `success`, `fail`, `traceId`.
- [ ] Implement `ErrorCode`, `BizException`, and `GlobalExceptionHandler`.
- [ ] Implement `UserContext` and `UserContextHolder`.

### Task 3: Security and JWT

**Files:**
- Create: `JwtProperties`, `JwtUtil`, `JwtAuthFilter`, `WebMvcConfig`.

- [ ] Implement HS256 JWT token generation and parsing.
- [ ] Implement request filter that validates `Authorization: Bearer ...`.
- [ ] Exclude `/api/auth/register`, `/api/auth/login`, `/actuator/**`, `/error`.

### Task 4: Persistence and config

**Files:**
- Create: `application.yml`, `logback-spring.xml`, mapper XML config, Redis config, WebClient config.
- Create MySQL init SQL under `deploy/sql/java-backend-init.sql`.

- [ ] Configure MySQL datasource with env defaults.
- [ ] Configure Redis template with JSON serializer.
- [ ] Configure multipart upload size and local file storage path.

### Task 5: User auth module

**Files:**
- Create: user entity, mapper, DTO/VO, service, controller.

- [ ] Register user with BCrypt password hash and unique username check.
- [ ] Login user and return JWT token plus user profile.
- [ ] Provide `/api/auth/me` endpoint using JWT context.

### Task 6: File module

**Files:**
- Create: file entity, mapper, VO, service, controller.

- [ ] Upload multipart file to local storage path.
- [ ] Save file metadata to MySQL.
- [ ] Provide authenticated metadata query and file download endpoint.

### Task 7: Resume and JD modules

**Files:**
- Create: resume/JD entities, mappers, DTO/VO, services, controllers.

- [ ] Implement create/list/detail/update/delete for resumes.
- [ ] Implement create/list/detail/update/delete for JDs.
- [ ] Scope all queries by current user id.

### Task 8: Python Agent and AI task module

**Files:**
- Create: `AgentClient`, `AgentRequest`, `AgentResponse`, `AgentProperties`.
- Create: AI task entity, mapper, DTO/VO, service, controller.

- [ ] Submit AI task with capability, biz id, and input JSON.
- [ ] Persist task as `PENDING`, call Python Agent through WebClient, then persist `SUCCESS` or `FAILED`.
- [ ] Cache task status in Redis with `ai:task:{taskUuid}`.
- [ ] Provide task detail and result query endpoints.

### Task 9: Conversation history module

**Files:**
- Create: conversation and message entities, mappers, DTO/VO, service, controller.

- [ ] Create/list conversations for current user.
- [ ] Add/list messages under a conversation.
- [ ] Store role, content, task uuid, and metadata JSON.

### Task 10: Verification

- [ ] Run `mvn -q test` in `agent-jd-java`.
- [ ] Run `mvn -q -DskipTests package` in `agent-jd-java`.
- [ ] Fix compile or test failures until both commands pass.
