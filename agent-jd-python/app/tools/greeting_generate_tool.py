from app.tools.jd_parser_tool import jd_parser_tool


def greeting_generate_tool(user_profile: dict, jd_text: str, channel: str = "boss") -> dict:
    jd = jd_parser_tool(jd_text)
    name = user_profile.get("name") or "候选人"
    target = jd.get("title_hint", "该岗位")
    skills = "、".join([item["name"] for item in jd["hard_skills"][:4]])
    content = f"您好，我是{name}，关注到贵司{target}岗位。我具备{skills or '相关技术'}经验，过往项目与岗位要求匹配度较高，期待有机会进一步沟通。"
    if channel == "email":
        content = f"您好，\n\n我是{name}。关注到贵司{target}岗位后，我认为自己的{skills or '项目'}经验与岗位要求较为匹配，随信希望获得进一步沟通机会。\n\n谢谢。"
    return {"channel": channel, "content": content, "jd_summary": jd["summary"]}
