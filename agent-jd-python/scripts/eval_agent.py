import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.agents.evaluation import MatchEvaluationCase, evaluate_match_cases
from app.agents.schemas import build_match_result
from app.core.settings import settings
from app.llm.factory import get_llm
from app.llm.fake_provider import FakeLLMProvider
from app.prompts import prompt_registry
from app.tools.match_analysis_tool import match_analysis_tool


def load_cases(path: Path) -> list[MatchEvaluationCase]:
    cases = []
    seen_ids = set()
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            item = json.loads(line)
            case_id = str(item["id"])
            if case_id in seen_ids:
                raise ValueError(f"Duplicate evaluation case id: {case_id}")
            seen_ids.add(case_id)
            cases.append(
                MatchEvaluationCase(
                    case_id=case_id,
                    resume_text=item["resume_text"],
                    jd_text=item["jd_text"],
                    expected_matched_skills=frozenset(item["expected_matched_skills"]),
                    expected_missing_skills=frozenset(item["expected_missing_skills"]),
                )
            )
    return cases


async def run_agent_evaluation(dataset: Path, provider: str) -> dict[str, Any]:
    llm = FakeLLMProvider() if provider == "fake" else get_llm()

    async def generate(case: MatchEvaluationCase) -> dict[str, Any]:
        base = match_analysis_tool(case.resume_text, case.jd_text)
        messages = prompt_registry.render(
            "match_analyze/v1",
            resume_text=case.resume_text,
            jd_text=case.jd_text,
            base_match=base,
        )
        ai_result = await llm.json_mode(messages, max_tokens=900)
        return build_match_result(base, ai_result).model_dump()

    result = await evaluate_match_cases(load_cases(dataset), generate)
    result.update(
        {
            "provider": provider if provider == "fake" else settings.llm_provider,
            "model": _model_name(provider),
        }
    )
    return result


def _model_name(provider: str) -> str:
    if provider == "fake":
        return "deterministic"
    if settings.llm_provider == "dashscope":
        return settings.dashscope_model
    return settings.openai_model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="eval/agent_match_dataset.jsonl")
    parser.add_argument("--provider", choices=["fake", "configured"], default="fake")
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()

    result = asyncio.run(run_agent_evaluation(Path(args.dataset), args.provider))
    if not args.details:
        result = {key: value for key, value in result.items() if key != "details"}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
