import asyncio
from time import perf_counter
from typing import Any

from app.core.metrics import record_llm_call
from app.core.settings import settings
from app.llm.base import LLMProvider


class FakeLLMProvider(LLMProvider):
    """Deterministic provider for local and CI end-to-end tests."""

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        started = perf_counter()
        try:
            await self._delay()
            result = self._chat_response(messages)
        except Exception:
            record_llm_call("fake", "deterministic", "chat", "failed", perf_counter() - started)
            raise
        record_llm_call("fake", "deterministic", "chat", "success", perf_counter() - started)
        return result

    async def json_mode(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        started = perf_counter()
        try:
            await self._delay()
            result = {
                "total_score": 82,
                "hard_score": 84,
                "soft_score": 78,
                "exp_score": 80,
                "suggestions": ["补充自动化测试证据", "说明 Redis 任务恢复机制"],
                "summary": "候选人的 Java、Redis 与 AI 应用经验和岗位要求具有较高匹配度。",
                "risks": ["需要进一步说明生产环境的监控与容量验证"],
                "advantages": ["具备完整的 Java 与 Python Agent 协作实践"],
            }
        except Exception:
            record_llm_call("fake", "deterministic", "json", "failed", perf_counter() - started)
            raise
        record_llm_call("fake", "deterministic", "json", "success", perf_counter() - started)
        return result

    def _chat_response(self, messages: list[dict[str, str]]) -> str:
        system_prompt = messages[0].get("content", "") if messages else ""
        full_prompt = "\n".join(message.get("content", "") for message in messages)

        if "AI 求职 Agent" in system_prompt:
            if "E2E_SECOND" in full_prompt and "E2E_FIRST" in full_prompt:
                return "FAKE_E2E_CONTEXT_OK：已读取上一轮对话，并给出第二轮求职建议。"
            return "FAKE_E2E_REPLY：已收到问题，我会基于现有简历和 JD 给出可执行建议。"

        if "项目经历" in system_prompt:
            return (
                "## STAR 改写版\n\n"
                "围绕目标岗位梳理项目职责，突出 Spring Boot、Redis 与 AI 任务链路。\n\n"
                "## 简历 bullet\n\n"
                "- 设计异步 AI 任务处理流程，并补充重试与失败恢复。\n"
                "- 拆分 Java 业务服务与 Python Agent 服务，保持职责清晰。\n\n"
                "## 面试亮点\n\n可重点说明可靠性设计、服务边界和验证方式。"
            )

        return (
            "## 匹配总结\n\n"
            "候选人的后端工程经验与目标岗位存在可验证的技能交集，描述应继续围绕已有事实展开。\n\n"
            "## 简历优化建议\n\n"
            "建议按问题、方案、职责和验证结果组织项目内容，明确 Java 服务、Python Agent、Redis 任务队列与 RAG 的边界。\n\n"
            "## 技能补强建议\n\n"
            "建议补充自动化测试、监控指标和故障恢复过程，避免添加输入中不存在的业务数据。\n\n"
            "## 项目描述优化方向\n\n"
            "使用可复现测试结果支撑可靠性描述，并保留关键技术取舍。"
        )

    async def _delay(self) -> None:
        delay_ms = max(0, settings.fake_llm_delay_ms)
        if delay_ms:
            await asyncio.sleep(delay_ms / 1000)
