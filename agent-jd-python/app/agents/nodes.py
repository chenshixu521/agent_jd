from app.infra.redis_client import append_event
from app.llm.factory import get_llm
from app.memory.schema import ChatMessage
from app.memory.session_store import get_session_store
from app.prompts import prompt_registry
from app.rag.retriever import abuild_prompt_context, aretrieve_hits
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
    hits = await aretrieve_hits(["jd", "project_template", "skill_keyword", "interview_question", "greeting_template"], query, top_k=6)
    examples = [hit.text for hit in hits]
    prompt_context = await abuild_prompt_context(["jd", "project_template", "skill_keyword", "interview_question"], query, top_k=6)
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
    result = {**base, **ai_result}
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
    return {**state, "project_text": project_text, "rewrite": result}


async def greeting_node(state: dict) -> dict:
    payload = state.get("payload", {})
    result = greeting_generate_tool(payload.get("user_profile", {}), state.get("jd_text", payload.get("jd_text", "")), payload.get("channel", "boss"))
    await emit(state, "greeting_generate", {"channel": result.get("channel")})
    return {**state, "greeting": result}


async def advice_node(state: dict) -> dict:
    messages = prompt_registry.render(
        "resume_optimize/v1",
        resume_text=truncate_text(state.get("resume_text", ""), 5000),
        jd_text=truncate_text(state.get("jd_text", ""), 2500),
        match=state.get("match", {}),
        examples=(state.get("rag_examples", []) or [])[:3],
        rag_context=truncate_text(state.get("rag_prompt_context", ""), 1200),
    )
    advice = await get_llm().chat(messages, max_tokens=900)
    await emit(state, "generate_advice", {"length": len(advice)})
    return {**state, "advice": advice}


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
        session = await store.create_session(title=payload.get("title", "求职 Agent 对话"))
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
    data = {
        "resume": state.get("parsed_resume"),
        "jd": state.get("parsed_jd"),
        "keywords": state.get("keywords"),
        "match": state.get("match"),
        "rewrite": state.get("rewrite"),
        "greeting": state.get("greeting"),
        "advice": state.get("advice"),
        "session_id": state.get("session_id"),
        "rag_examples": state.get("rag_examples", []),
        "events": state.get("events", []),
    }
    data = {k: v for k, v in data.items() if v not in (None, [], {})}
    await emit(state, "finalize", {"keys": list(data.keys())})
    return {**state, "final": data}
