from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    task_id: str
    capability: str
    action: str
    payload: dict[str, Any]
    resume_text: str
    jd_text: str
    project_text: str
    user_profile: dict[str, Any]
    conversation: list[dict[str, str]]
    parsed_resume: dict[str, Any]
    parsed_jd: dict[str, Any]
    keywords: dict[str, Any]
    match: dict[str, Any]
    rewrite: dict[str, Any]
    greeting: dict[str, Any]
    advice: str
    rag_examples: list[str]
    final: dict[str, Any]
    events: list[dict[str, Any]]
