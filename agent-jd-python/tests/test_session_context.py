from app.memory.context_window import ContextWindowPolicy
from app.memory.schema import ChatMessage
from app.memory.session_store import RedisSessionStore


def test_context_window_keeps_recent_messages_within_token_budget():
    policy = ContextWindowPolicy(max_tokens=18, reserve_tokens=4)
    messages = [
        ChatMessage(role="user", content="第一轮 我 有 Java 经验"),
        ChatMessage(role="assistant", content="好的 已记录 Java 经验"),
        ChatMessage(role="user", content="第二轮 我 会 Redis"),
        ChatMessage(role="assistant", content="好的 已记录 Redis"),
        ChatMessage(role="user", content="第三轮 请 匹配 JD"),
    ]

    trimmed = policy.trim(messages)

    assert len(trimmed) < len(messages)
    assert trimmed[-1].content == "第三轮 请 匹配 JD"
    assert sum(policy.count_tokens(item.content) for item in trimmed) <= 14


async def test_session_store_uses_task_id_for_retry_safe_session(monkeypatch):
    store = RedisSessionStore()

    async def ignore_save(_state):
        return None

    monkeypatch.setattr(store, "save_session", ignore_save)

    state = await store.create_session(user_id="user-1", session_id="task-1")

    assert state.session_id == "task-1"
