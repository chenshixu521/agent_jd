from app.tools.keyword_extract_tool import keyword_extract_tool

SOFT_SKILLS = ["沟通", "协作", "团队", "抗压", "学习能力", "责任心", "主动性", "表达"]


def jd_parser_tool(jd_text: str) -> dict:
    text = jd_text or ""
    keywords = keyword_extract_tool(text)["keywords"]
    hard_skills = [{"name": item, "weight": 0.9 if item in ["Java", "Python", "Spring Boot", "LangGraph"] else 0.75} for item in keywords]
    soft_skills = [item for item in SOFT_SKILLS if item in text]
    title_hint = "Java 后端工程师" if "Java" in keywords else "AI 应用工程师" if "LangGraph" in keywords or "RAG" in keywords else "软件工程师"
    bonus = []
    for hint in ["高并发", "分布式", "微服务", "AI", "RAG", "Agent"]:
        if hint in text:
            bonus.append(f"有{hint}经验")
    return {
        "title_hint": title_hint,
        "hard_skills": hard_skills,
        "soft_skills": soft_skills,
        "bonus": bonus,
        "summary": text[:300],
    }
