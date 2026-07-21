from app.agents.evaluation import MatchEvaluationCase, assess_match_result, evaluate_match_cases
from app.agents.schemas import build_match_result
from app.tools.match_analysis_tool import match_analysis_tool


def case() -> MatchEvaluationCase:
    return MatchEvaluationCase(
        case_id="java-match",
        resume_text="使用 Java、Spring Boot 和 Redis 开发后端服务。",
        jd_text="要求 Java、Spring Boot、Redis 和 Kafka。",
        expected_matched_skills=frozenset({"Java", "Spring Boot", "Redis"}),
        expected_missing_skills=frozenset({"Kafka"}),
    )


def test_assess_match_result_checks_labels_grounding_and_evidence():
    evaluation_case = case()
    base = match_analysis_tool(evaluation_case.resume_text, evaluation_case.jd_text)
    result = build_match_result(base, {"matched_skills": ["未支持技能"], "missing_skills": []})

    assessment = assess_match_result(evaluation_case, result)

    assert assessment["label_exact_match"] is True
    assert assessment["grounded_claims"] == 4
    assert assessment["total_claims"] == 4
    assert assessment["covered_claims"] == 4


async def test_evaluate_match_cases_reports_structured_failure():
    async def invalid_generator(_case: MatchEvaluationCase):
        return {"total_score": "invalid"}

    result = await evaluate_match_cases([case()], invalid_generator)

    assert result["structured_output_success_rate"] == 0.0
    assert result["skill_label_exact_match_rate"] == 0.0
    assert result["details"][0]["structured"] is False
