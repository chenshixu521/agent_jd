from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.agents.schemas import MatchResult
from app.tools.jd_parser_tool import jd_parser_tool
from app.tools.resume_parser_tool import resume_parser_tool


@dataclass(frozen=True)
class MatchEvaluationCase:
    case_id: str
    resume_text: str
    jd_text: str
    expected_matched_skills: frozenset[str]
    expected_missing_skills: frozenset[str]


MatchGenerator = Callable[[MatchEvaluationCase], Awaitable[dict[str, Any]]]


async def evaluate_match_cases(cases: list[MatchEvaluationCase], generator: MatchGenerator) -> dict[str, Any]:
    details = []
    structured_successes = 0
    label_exact_matches = 0
    grounded_claims = 0
    total_claims = 0
    covered_claims = 0

    for case in cases:
        try:
            raw_result = await generator(case)
            result = MatchResult.model_validate(raw_result)
        except Exception as exc:
            details.append({"id": case.case_id, "structured": False, "error": type(exc).__name__})
            continue

        structured_successes += 1
        assessment = assess_match_result(case, result)
        label_exact_matches += int(assessment["label_exact_match"])
        grounded_claims += assessment["grounded_claims"]
        total_claims += assessment["total_claims"]
        covered_claims += assessment["covered_claims"]
        details.append({"id": case.case_id, "structured": True, **assessment})

    size = len(cases)
    return {
        "cases": size,
        "structured_output_success_rate": _ratio(structured_successes, size),
        "skill_label_exact_match_rate": _ratio(label_exact_matches, size),
        "grounded_skill_claim_rate": _ratio(grounded_claims, total_claims),
        "evidence_coverage_rate": _ratio(covered_claims, total_claims),
        "details": details,
    }


def assess_match_result(case: MatchEvaluationCase, result: MatchResult) -> dict[str, Any]:
    resume_skills = set(resume_parser_tool(case.resume_text)["skills"])
    jd_skills = {item["name"] for item in jd_parser_tool(case.jd_text)["hard_skills"]}
    predicted_matched = set(result.matched_skills)
    predicted_missing = set(result.missing_skills)
    matched_grounded = {skill for skill in predicted_matched if skill in resume_skills and skill in jd_skills}
    missing_grounded = {skill for skill in predicted_missing if skill in jd_skills and skill not in resume_skills}
    claims = [("matched_skills", "rule", skill) for skill in predicted_matched]
    claims.extend(("missing_skills", "jd", skill) for skill in predicted_missing)
    covered_claims = sum(
        any(item.field == field and item.source == source and skill in item.content for item in result.evidence)
        for field, source, skill in claims
    )
    return {
        "label_exact_match": (
            predicted_matched == case.expected_matched_skills
            and predicted_missing == case.expected_missing_skills
        ),
        "expected_matched": sorted(case.expected_matched_skills),
        "predicted_matched": sorted(predicted_matched),
        "expected_missing": sorted(case.expected_missing_skills),
        "predicted_missing": sorted(predicted_missing),
        "grounded_claims": len(matched_grounded) + len(missing_grounded),
        "total_claims": len(claims),
        "covered_claims": covered_claims,
    }


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0
