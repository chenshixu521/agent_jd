from langgraph.graph import END, StateGraph

from app.agents.nodes import (
    advice_node,
    chat_node,
    extract_keywords_node,
    finalize_node,
    greeting_node,
    match_node,
    parse_jd_node,
    parse_resume_node,
    retrieve_rag_node,
    rewrite_project_node,
)
from app.agents.state import AgentState


def build_resume_optimize_graph():
    graph = StateGraph(AgentState)
    graph.add_node("parse_resume", parse_resume_node)
    graph.add_node("parse_jd", parse_jd_node)
    graph.add_node("extract_keywords", extract_keywords_node)
    graph.add_node("rag", retrieve_rag_node)
    graph.add_node("match_analysis", match_node)
    graph.add_node("generate_advice", advice_node)
    graph.add_node("finalize", finalize_node)
    graph.set_entry_point("parse_resume")
    graph.add_edge("parse_resume", "parse_jd")
    graph.add_edge("parse_jd", "extract_keywords")
    graph.add_edge("extract_keywords", "rag")
    graph.add_edge("rag", "match_analysis")
    graph.add_edge("match_analysis", "generate_advice")
    graph.add_edge("generate_advice", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


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
