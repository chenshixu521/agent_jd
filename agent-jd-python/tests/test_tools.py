from app.tools.keyword_extract_tool import keyword_extract_tool
from app.tools.jd_parser_tool import jd_parser_tool


def test_keyword_extract_tool_extracts_known_skills():
    text = "岗位要求：熟悉 Java、Spring Boot、MySQL、Redis，有 LangChain 或 LangGraph 项目经验。"

    result = keyword_extract_tool(text)

    assert "Java" in result["keywords"]
    assert "Spring Boot" in result["keywords"]
    assert "MySQL" in result["keywords"]
    assert "Redis" in result["keywords"]


def test_jd_parser_tool_returns_structured_result():
    text = "招聘 Java 后端工程师，要求 Spring Boot、MySQL、Redis，具备沟通能力和团队协作能力。"

    result = jd_parser_tool(text)

    assert result["title_hint"] == "Java 后端工程师"
    assert "Spring Boot" in [item["name"] for item in result["hard_skills"]]
    assert "沟通" in result["soft_skills"]
