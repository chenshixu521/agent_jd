from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import gevent
from locust import HttpUser, between, events, task


class AgentJdUser(HttpUser):
    wait_time = between(0.05, 0.2)

    def on_start(self) -> None:
        suffix = uuid4().hex[:16]
        with self.client.post(
            "/api/auth/register",
            json={
                "username": f"load_{suffix}",
                "password": "LoadTest_2026",
                "email": f"load_{suffix}@example.test",
            },
            name="POST /api/auth/register",
            catch_response=True,
        ) as response:
            payload = self._json(response)
            if response.status_code != 200 or payload.get("code") != 0 or not payload.get("data", {}).get("accessToken"):
                response.failure(f"registration failed: HTTP {response.status_code} {response.text[:200]}")
                self.token = None
                return
            self.token = payload["data"]["accessToken"]

    @task
    def match_task_workflow(self) -> None:
        if not self.token:
            gevent.sleep(0.2)
            return

        started = perf_counter()
        failure: Exception | None = None
        try:
            task_uuid = self._submit_task()
            self._wait_for_success(task_uuid)
        except Exception as exc:
            failure = exc
        elapsed_ms = (perf_counter() - started) * 1000
        events.request.fire(
            request_type="TASK",
            name="match task end-to-end",
            response_time=elapsed_ms,
            response_length=0,
            exception=failure,
        )

    def _submit_task(self) -> str:
        with self.client.post(
            "/api/tasks",
            headers=self._headers(),
            json={
                "capability": "match",
                "action": "analyze",
                "input": {
                    "resume_text": "Java 后端工程师，使用 Spring Boot、MySQL、Redis，并参与 AI Agent 异步任务建设。",
                    "jd_text": "招聘 Java 后端工程师，要求 Spring Boot、MySQL、Redis 和异步任务经验。",
                },
            },
            name="POST /api/tasks",
            catch_response=True,
        ) as response:
            payload = self._json(response)
            task_uuid = payload.get("data", {}).get("taskUuid")
            if response.status_code != 200 or payload.get("code") != 0 or not task_uuid:
                message = f"task submission failed: HTTP {response.status_code} {response.text[:200]}"
                response.failure(message)
                raise RuntimeError(message)
            return str(task_uuid)

    def _wait_for_success(self, task_uuid: str) -> None:
        deadline = perf_counter() + 30
        while perf_counter() < deadline:
            with self.client.get(
                f"/api/tasks/{task_uuid}/result",
                headers=self._headers(),
                name="GET /api/tasks/:taskUuid/result",
                catch_response=True,
            ) as response:
                payload = self._json(response)
                if response.status_code != 200 or payload.get("code") != 0:
                    message = f"task polling failed: HTTP {response.status_code} {response.text[:200]}"
                    response.failure(message)
                    raise RuntimeError(message)
                status = payload.get("data", {}).get("status")
                if status == 2:
                    return
                if status in {3, 4}:
                    raise RuntimeError(f"task reached terminal failure status {status}")
            gevent.sleep(0.1)
        raise TimeoutError(f"task {task_uuid} did not finish in 30 seconds")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _json(self, response) -> dict:
        try:
            return response.json()
        except ValueError:
            return {}


@events.quitting.add_listener
def enforce_thresholds(environment, **_kwargs) -> None:
    total = environment.stats.total
    task_stats = environment.stats.entries.get(("match task end-to-end", "TASK"))
    failed = total.fail_ratio >= 0.01
    if task_stats is None or task_stats.num_requests == 0:
        failed = True
    elif task_stats.get_response_time_percentile(0.95) >= 5000:
        failed = True
    if failed:
        environment.process_exit_code = 1
