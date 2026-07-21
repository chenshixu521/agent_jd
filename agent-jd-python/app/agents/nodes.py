import re

from app.agents.schemas import build_match_result
from app.infra.redis_client import append_event
from app.llm.factory import get_llm
from app.memory.schema import ChatMessage
from app.memory.session_store import get_session_store
from app.prompts import prompt_registry
from app.rag.prompt_enhancer import PromptEnhancer
from app.rag.retriever import aretrieve_hits
from app.tools.greeting_generate_tool import greeting_generate_tool
from app.tools.jd_parser_tool import jd_parser_tool
from app.tools.keyword_extract_tool import keyword_extract_tool
from app.tools.match_analysis_tool import match_analysis_tool
from app.tools.project_rewrite_tool import project_rewrite_tool
from app.tools.resume_parser_tool import resume_parser_tool


async def emit(state: dict, stage: str, payload: dict | None = None) -> None:
    task_id = state.get("task_id") or "unknown"
    event = {"stage": stage, "payload": payload or {}}
    state.setdefault("events", []).append(event)
    await append_event(task_id, event)


async def validate_resume_optimize_input_node(state: dict) -> dict:
    resume_text = (state.get("resume_text") or state.get("payload", {}).get("resume_text", "")).strip()
    jd_text = (state.get("jd_text") or state.get("payload", {}).get("jd_text", "")).strip()
    missing_fields = []
    if len(resume_text) < 40:
        missing_fields.append("resume_text")
    if len(jd_text) < 20:
        missing_fields.append("jd_text")
    await emit(state, "validate_input", {"valid": not missing_fields, "missing_fields": missing_fields})
    return {
        **state,
        "resume_text": resume_text,
        "jd_text": jd_text,
        "input_valid": not missing_fields,
        "missing_fields": missing_fields,
    }


async def clarify_input_node(state: dict) -> dict:
    labels = {"resume_text": "完整简历正文", "jd_text": "目标岗位 JD"}
    missing = [labels.get(item, item) for item in state.get("missing_fields", [])]
    questions = "\n".join(f"- 请补充{item}，避免在信息不足时生成泛化建议。" for item in missing)
    clarification = f"## 需要补充信息\n\n{questions}"
    await emit(state, "clarify_input", {"missing_fields": state.get("missing_fields", [])})
    return {**state, "clarification": clarification, "advice": clarification, "output_valid": True}


async def parse_resume_node(state: dict) -> dict:
    resume_text = state.get("resume_text") or state.get("payload", {}).get("resume_text", "")
    parsed = resume_parser_tool(resume_text)
    await emit(state, "parse_resume", {"skills": parsed.get("skills", [])})
    return {**state, "resume_text": resume_text, "parsed_resume": parsed}


async def parse_jd_node(state: dict) -> dict:
    jd_text = state.get("jd_text") or state.get("payload", {}).get("jd_text", "")
    parsed = jd_parser_tool(jd_text)
    await emit(state, "parse_jd", {"hard_skills": parsed.get("hard_skills", [])})
    return {**state, "jd_text": jd_text, "parsed_jd": parsed}


async def extract_keywords_node(state: dict) -> dict:
    text = "\n".join([state.get("resume_text", ""), state.get("jd_text", ""), state.get("project_text", "")])
    result = keyword_extract_tool(text)
    await emit(state, "extract_keywords", result)
    return {**state, "keywords": result}


async def retrieve_rag_node(state: dict) -> dict:
    query = "\n".join([state.get("jd_text", ""), state.get("resume_text", ""), state.get("project_text", "")])
    hits = await aretrieve_hits(["jd", "project_template", "skill_keyword", "interview_question"], query, top_k=6)
    examples = [hit.text for hit in hits]
    prompt_context = PromptEnhancer().build_context(query, hits)
    await emit(state, "retrieve_rag", {"count": len(examples), "kbs": sorted({hit.kb for hit in hits})})
    return {**state, "rag_examples": examples, "rag_hits": hits, "rag_prompt_context": prompt_context}


async def match_node(state: dict) -> dict:
    base = match_analysis_tool(state.get("resume_text", ""), state.get("jd_text", ""))
    messages = prompt_registry.render(
        "match_analyze/v1",
        resume_text=truncate_text(state.get("resume_text", ""), 5000),
        jd_text=truncate_text(state.get("jd_text", ""), 2500),
        base_match=base,
    )
    ai_result = await get_llm().json_mode(messages, max_tokens=900)
    result = build_match_result(base, ai_result).model_dump()
    await emit(state, "match_analysis", {"score": result.get("total_score")})
    return {**state, "match": result}


async def rewrite_project_node(state: dict) -> dict:
    project_text = state.get("project_text") or state.get("payload", {}).get("project_text", "")
    hits = await aretrieve_hits(["project_template", "skill_keyword", "interview_question"], project_text + "\n" + state.get("jd_text", ""), top_k=3)
    base = project_rewrite_tool(project_text, state.get("jd_text", ""), examples=[hit.text for hit in hits])
    messages = prompt_registry.render(
        "project_rewrite/v1",
        project_text=truncate_text(project_text, 4000),
        jd_text=truncate_text(state.get("jd_text", ""), 2500),
        base_rewrite=base,
        examples=[hit.text for hit in hits],
    )
    rewritten = await get_llm().chat(messages, max_tokens=900)
    result = {**base, "rewritten": rewritten}
    await emit(state, "project_rewrite", {"skills": result.get("skills", [])})
    return {**state, "project_text": project_text, "rewrite": result, "rag_hits": hits}


async def greeting_node(state: dict) -> dict:
    payload = state.get("payload", {})
    result = greeting_generate_tool(payload.get("user_profile", {}), state.get("jd_text", payload.get("jd_text", "")), payload.get("channel", "boss"))
    await emit(state, "greeting_generate", {"channel": result.get("channel")})
    return {**state, "greeting": result}


async def advice_node(state: dict) -> dict:
    attempts = state.get("generation_attempts", 0) + 1
    messages = prompt_registry.render(
        "resume_optimize/v1",
        resume_text=truncate_text(state.get("resume_text", ""), 5000),
        jd_text=truncate_text(state.get("jd_text", ""), 2500),
        match=state.get("match", {}),
        examples=(state.get("rag_examples", []) or [])[:3],
        rag_context=truncate_text(state.get("rag_prompt_context", ""), 1200),
        validation_feedback=state.get("validation_feedback", []),
    )
    advice = await get_llm().chat(messages, max_tokens=900)
    await emit(state, "generate_advice", {"length": len(advice), "attempt": attempts})
    return {**state, "advice": advice, "generation_attempts": attempts}


async def validate_advice_node(state: dict) -> dict:
    advice = (state.get("advice") or "").strip()
    feedback: list[str] = []
    if len(advice) < 120:
        feedback.append("输出过短，需要提供可执行的匹配总结和简历优化建议")
    if "建议" not in advice and "优化" not in advice:
        feedback.append("输出缺少明确的优化建议")

    metric_pattern = r"\d+(?:\.\d+)?%"
    grounded_metrics = set(re.findall(metric_pattern, "\n".join([state.get("resume_text", ""), state.get("jd_text", "")])))
    for field in ("total_score", "hard_score", "soft_score", "exp_score"):
        value = state.get("match", {}).get(field)
        if isinstance(value, (int, float)):
            grounded_metrics.update({f"{value}%", f"{value:g}%"})
    ungrounded_metrics = sorted(set(re.findall(metric_pattern, advice)) - grounded_metrics)
    if ungrounded_metrics:
        feedback.append(f"发现无输入依据的量化指标：{', '.join(ungrounded_metrics)}；不得编造结果数据")

    valid = not feedback
    await emit(state, "validate_advice", {"valid": valid, "feedback": feedback})
    return {**state, "output_valid": valid, "validation_feedback": feedback}


def truncate_text(text: str, limit: int) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n……（内容已截断，仅保留关键前文用于快速分析）"


async def chat_node(state: dict) -> dict:
    payload = state.get("payload", {})
    store = get_session_store()
    session_id = payload.get("session_id") or payload.get("sessionId")
    if not session_id:
        session = await store.create_session(
            title=payload.get("title", "求职 Agent 对话"),
            session_id=state.get("task_id"),
        )
        session_id = session.session_id
    question = payload.get("message", "")
    conversation_messages = await store.build_context(session_id)
    conversation = [item.to_dict() for item in conversation_messages]
    messages = prompt_registry.render("chat/v1", conversation=conversation, message=question)
    cache_key = store.make_prompt_cache_key("chat", "v1", {"session_id": session_id, "conversation": conversation, "message": question})
    cached = await store.get_prompt_cache(cache_key)
    if cached is not None:
        answer = cached["answer"]
        await emit(state, "chat_cache_hit", {"session_id": session_id})
    else:
        answer = await get_llm().chat(messages)
        await store.set_prompt_cache(cache_key, {"answer": answer})
    if question:
        await store.append_message(session_id, ChatMessage(role="user", content=question, metadata={"task_id": state.get("task_id")}))
    await store.append_message(session_id, ChatMessage(role="assistant", content=answer, metadata={"task_id": state.get("task_id")}))
    await emit(state, "chat", {"length": len(answer)})
    return {**state, "session_id": session_id, "conversation": conversation, "advice": answer}


async def finalize_node(state: dict) -> dict:
    sources = []
    for hit in state.get("rag_hits", []) or []:
        sources.append(
            {
                "kb": hit.kb,
                "doc_id": hit.doc_id,
                "chunk_id": hit.chunk_id,
                "score": round(hit.score, 4),
                "text": truncate_text(hit.text, 240),
            }
        )
    data = {
        "resume": state.get("parsed_resume"),
        "jd": state.get("parsed_jd"),
        "keywords": state.get("keywords"),
        "match": state.get("match"),
        "rewrite": state.get("rewrite"),
        "greeting": state.get("greeting"),
        "advice": state.get("advice"),
        "clarification": state.get("clarification"),
        "session_id": state.get("session_id"),
        "rag_examples": state.get("rag_examples", []),
        "sources": sources,
        "validation": {
            "valid": state.get("output_valid"),
            "feedback": state.get("validation_feedback", []),
            "attempts": state.get("generation_attempts", 0),
        }
        if state.get("capability") == "resume" and state.get("action") in {"optimize", "advice"}
        else None,
        "events": state.get("events", []),
    }
    data = {k: v for k, v in data.items() if v not in (None, [], {})}
    await emit(state, "finalize", {"keys": list(data.keys())})
    return {**state, "final": data}
