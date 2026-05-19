from app.agents.graphs import (
    build_chat_graph,
    build_greeting_graph,
    build_jd_analyze_graph,
    build_match_graph,
    build_project_rewrite_graph,
    build_resume_optimize_graph,
)
from app.core.errors import AgentError, ErrorCode
from app.tools.keyword_extract_tool import keyword_extract_tool
from app.tools.resume_parser_tool import resume_parser_tool

_graph_cache = {}


def get_graph(capability: str, action: str):
    key = f"{capability}:{action}"
    if key in _graph_cache:
        return _graph_cache[key]
    if capability == "resume" and action in {"optimize", "advice"}:
        graph = build_resume_optimize_graph()
    elif capability == "resume" and action == "parse":
        graph = None
    elif capability == "jd" and action in {"analyze", "parse"}:
        graph = build_jd_analyze_graph()
    elif capability == "keyword" and action == "extract":
        graph = None
    elif capability == "project" and action == "rewrite":
        graph = build_project_rewrite_graph()
    elif capability == "match" and action == "analyze":
        graph = build_match_graph()
    elif capability == "greeting" and action == "generate":
        graph = build_greeting_graph()
    elif capability == "chat" and action in {"message", "talk"}:
        graph = build_chat_graph()
    else:
        raise AgentError(ErrorCode.NOT_FOUND, f"未知 Agent 能力: {key}")
    _graph_cache[key] = graph
    return graph


async def run_agent(capability: str, action: str, task_id: str, payload: dict) -> dict:
    if capability == "resume" and action == "parse":
        return {"resume": resume_parser_tool(payload.get("resume_text", ""))}
    if capability == "keyword" and action == "extract":
        return {"keywords": keyword_extract_tool(payload.get("text", ""))}
    graph = get_graph(capability, action)
    state = {
        "task_id": task_id,
        "capability": capability,
        "action": action,
        "payload": payload,
        "resume_text": payload.get("resume_text", ""),
        "jd_text": payload.get("jd_text", ""),
        "project_text": payload.get("project_text", ""),
        "user_profile": payload.get("user_profile", {}),
    }
    result = await graph.ainvoke(state)
    return result.get("final", result)
