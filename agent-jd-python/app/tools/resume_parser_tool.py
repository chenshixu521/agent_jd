from app.tools.keyword_extract_tool import keyword_extract_tool

SECTION_HINTS = {
    "basic": ["姓名", "电话", "邮箱", "年龄"],
    "education": ["教育", "学历", "本科", "硕士", "大学"],
    "work": ["工作经历", "任职", "公司", "负责"],
    "project": ["项目经历", "项目", "系统", "平台"],
    "skills": ["技能", "技术栈", "熟悉", "掌握"],
}


def resume_parser_tool(resume_text: str) -> dict:
    text = resume_text or ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections = {key: [] for key in SECTION_HINTS}
    for line in lines:
        matched = False
        for section, hints in SECTION_HINTS.items():
            if any(hint in line for hint in hints):
                sections[section].append(line)
                matched = True
        if not matched and len(line) > 20:
            sections["project"].append(line)
    return {
        "summary": text[:300],
        "sections": sections,
        "skills": keyword_extract_tool(text)["keywords"],
        "line_count": len(lines),
    }
