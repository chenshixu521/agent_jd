from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Evidence(BaseModel):
    source: Literal["resume", "jd", "rag", "rule"]
    field: str
    content: str


class MatchResult(BaseModel):
    total_score: float = Field(ge=0, le=100)
    hard_score: float = Field(ge=0, le=100)
    soft_score: float = Field(ge=0, le=100)
    exp_score: float = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    summary: str = ""
    risks: list[str] = Field(default_factory=list)
    advantages: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    @field_validator("matched_skills", "missing_skills", "suggestions", "risks", "advantages", mode="before")
    @classmethod
    def normalize_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return [str(item) for item in value if str(item).strip()]


def build_match_result(base: dict[str, Any], ai_result: dict[str, Any]) -> MatchResult:
    merged = {**base, **(ai_result or {})}
    for field in ("total_score", "hard_score", "soft_score", "exp_score"):
        merged[field] = _score(merged.get(field, base.get(field, 0)))

    # Skill evidence comes from deterministic keyword comparison, so an LLM
    # response cannot turn an unsupported skill into a rule-backed fact.
    matched = _strings(base.get("matched_skills", merged.get("matched_skills")))
    missing = _strings(base.get("missing_skills", merged.get("missing_skills")))
    evidence = [
        Evidence(source="rule", field="matched_skills", content=f"{skill} 同时出现在简历与 JD 技能关键词中")
        for skill in matched
    ]
    evidence.extend(
        Evidence(source="jd", field="missing_skills", content=f"JD 要求 {skill}，简历关键词中未检出")
        for skill in missing
    )
    merged["matched_skills"] = matched
    merged["missing_skills"] = missing
    merged["evidence"] = evidence
    return MatchResult.model_validate(merged)


def _score(value: Any) -> float:
    try:
        return round(min(100.0, max(0.0, float(value))), 2)
    except (TypeError, ValueError):
        return 0.0


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value if str(item).strip()]
