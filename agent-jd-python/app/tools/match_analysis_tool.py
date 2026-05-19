from app.tools.jd_parser_tool import jd_parser_tool
from app.tools.resume_parser_tool import resume_parser_tool


def match_analysis_tool(resume_text: str, jd_text: str) -> dict:
    resume = resume_parser_tool(resume_text)
    jd = jd_parser_tool(jd_text)
    resume_skills = set(resume["skills"])
    jd_skills = {item["name"] for item in jd["hard_skills"]}
    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)
    hard_score = 100.0 if not jd_skills else round(len(matched) / len(jd_skills) * 100, 2)
    soft_score = 80.0 if jd["soft_skills"] else 65.0
    exp_score = 75.0 if len(resume_text or "") > 300 else 55.0
    total_score = round(hard_score * 0.6 + soft_score * 0.2 + exp_score * 0.2, 2)
    return {
        "total_score": total_score,
        "hard_score": hard_score,
        "soft_score": soft_score,
        "exp_score": exp_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "suggestions": [f"补充 {item} 相关项目经验" for item in missing[:5]],
    }
