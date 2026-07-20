from langgraph.graph import END, StateGraph

from app.agents.nodes import (
    advice_node,
    chat_node,
    clarify_input_node,
    extract_keywords_node,
    finalize_node,
    greeting_node,
    match_node,
    parse_jd_node,
    parse_resume_node,
    retrieve_rag_node,
    rewrite_project_node,
    validate_advice_node,
    validate_resume_optimize_input_node,
)
from app.agents.state import AgentState


def build_resume_optimize_graph():
    graph = StateGraph(AgentState)
    graph.add_node("validate_input", validate_resume_optimize_input_node)
    graph.add_node("clarify_input", clarify_input_node)
    graph.add_node("parse_resume", parse_resume_node)
    graph.add_node("parse_jd", parse_jd_node)
    graph.add_node("extract_keywords", extract_keywords_node)
    graph.add_node("rag", retrieve_rag_node)
    graph.add_node("match_analysis", match_node)
    graph.add_node("generate_advice", advice_node)
    graph.add_node("validate_advice", validate_advice_node)
    graph.add_node("finalize", finalize_node)
    graph.set_entry_point("validate_input")
    graph.add_conditional_edges(
        "validate_input",
        route_resume_optimize_input,
        {"parse_resume": "parse_resume", "clarify_input": "clarify_input"},
    )
    graph.add_edge("clarify_input", "finalize")
    graph.add_edge("parse_resume", "parse_jd")
    graph.add_edge("parse_jd", "extract_keywords")
    graph.add_edge("extract_keywords", "rag")
    graph.add_edge("rag", "match_analysis")
    graph.add_edge("match_analysis", "generate_advice")
    graph.add_edge("generate_advice", "validate_advice")
    graph.add_conditional_edges(
        "validate_advice",
        route_resume_optimize_output,
        {"generate_advice": "generate_advice", "finalize": "finalize"},
    )
    graph.add_edge("finalize", END)
    return graph.compile()


def route_resume_optimize_input(state: AgentState) -> str:
    return "parse_resume" if state.get("input_valid") else "clarify_input"


def route_resume_optimize_output(state: AgentState) -> str:
    if state.get("output_valid") or state.get("generation_attempts", 0) >= 2:
        return "finalize"
    return "generate_advice"


def build_jd_analyze_graph():
    graph = StateGraph(AgentState)
    graph.add_node("parse_jd", parse_jd_node)
    graph.add_node("extract_keywords", extract_keywords_node)
    graph.add_node("finalize", finalize_node)
    graph.set_entry_point("parse_jd")
    graph.add_edge("parse_jd", "extract_keywords")
    graph.add_edge("extract_keywords", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def build_project_rewrite_graph():
    graph = StateGraph(AgentState)
    graph.add_node("parse_jd", parse_jd_node)
    graph.add_node("project_rewrite", rewrite_project_node)
    graph.add_node("finalize", finalize_node)
    graph.set_entry_point("parse_jd")
    graph.add_edge("parse_jd", "project_rewrite")
    graph.add_edge("project_rewrite", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def build_match_graph():
    graph = StateGraph(AgentState)
    graph.add_node("parse_resume", parse_resume_node)
    graph.add_node("parse_jd", parse_jd_node)
    graph.add_node("match_analysis", match_node)
    graph.add_node("finalize", finalize_node)
    graph.set_entry_point("parse_resume")
    graph.add_edge("parse_resume", "parse_jd")
    graph.add_edge("parse_jd", "match_analysis")
    graph.add_edge("match_analysis", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def build_greeting_graph():
    graph = StateGraph(AgentState)
    graph.add_node("parse_jd", parse_jd_node)
    graph.add_node("greeting_generate", greeting_node)
    graph.add_node("finalize", finalize_node)
    graph.set_entry_point("parse_jd")
    graph.add_edge("parse_jd", "greeting_generate")
    graph.add_edge("greeting_generate", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def build_chat_graph():
    graph = StateGraph(AgentState)
    graph.add_node("chat", chat_node)
    graph.add_node("finalize", finalize_node)
    graph.set_entry_point("chat")
    graph.add_edge("chat", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()
