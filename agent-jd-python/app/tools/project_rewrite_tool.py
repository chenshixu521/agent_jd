from app.tools.keyword_extract_tool import keyword_extract_tool


def project_rewrite_tool(project_text: str, jd_text: str = "", examples: list[str] | None = None) -> dict:
    skills = keyword_extract_tool(project_text + "\n" + jd_text)["keywords"]
    rewritten = (
        "项目背景：围绕业务效率与系统稳定性建设核心能力。\n"
        f"任务职责：负责 {', '.join(skills[:6]) or '后端核心模块'} 的方案设计、接口开发与性能优化。\n"
        "行动过程：梳理业务流程，拆分服务边界，设计数据模型与异常处理机制，并通过缓存、异步任务和日志追踪提升可维护性。\n"
        "结果产出：提升系统可用性与交付效率，形成可复用的工程化实践。"
    )
    return {"rewritten": rewritten, "skills": skills, "examples": examples or []}
