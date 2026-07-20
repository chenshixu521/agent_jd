from app.agents.graphs import build_resume_optimize_graph
from app.agents.nodes import validate_advice_node, validate_resume_optimize_input_node
from app.agents.schemas import build_match_result


async def test_resume_optimize_requests_clarification_for_incomplete_input(monkeypatch):
    async def ignore_event(*_args, **_kwargs):
        return None

    monkeypatch.setattr("app.agents.nodes.append_event", ignore_event)
    state = await validate_resume_optimize_input_node(
        {"task_id": "test", "payload": {"resume_text": "Java", "jd_text": "招聘 Java"}}
    )

    assert state["input_valid"] is False
    assert state["missing_fields"] == ["resume_text", "jd_text"]


async def test_resume_optimize_graph_short_circuits_incomplete_input(monkeypatch):
    async def ignore_event(*_args, **_kwargs):
        return None

    def fail_if_llm_is_called():
        raise AssertionError("incomplete input must not invoke the LLM")

    monkeypatch.setattr("app.agents.nodes.append_event", ignore_event)
    monkeypatch.setattr("app.agents.nodes.get_llm", fail_if_llm_is_called)
    result = await build_resume_optimize_graph().ainvoke(
        {
            "task_id": "test",
            "capability": "resume",
            "action": "optimize",
            "payload": {"resume_text": "Java", "jd_text": "招聘 Java"},
        }
    )

    assert result["final"]["validation"] == {"valid": True, "feedback": [], "attempts": 0}
    assert "完整简历正文" in result["final"]["clarification"]


async def test_advice_validation_rejects_ungrounded_metrics(monkeypatch):
    async def ignore_event(*_args, **_kwargs):
        return None

    monkeypatch.setattr("app.agents.nodes.append_event", ignore_event)
    state = await validate_advice_node(
        {
            "task_id": "test",
            "resume_text": "负责 Java 后端服务开发和 Redis 缓存建设。" * 5,
            "jd_text": "招聘 Java 后端工程师，要求 Spring Boot、MySQL 和 Redis。",
            "match": {"total_score": 80},
            "advice": "## 匹配总结\n候选人具备 Java 和 Redis 经验。\n\n## 优化建议\n建议写成性能提升 35%，以增强项目说服力。" * 3,
        }
    )

    assert state["output_valid"] is False
    assert any("35%" in item for item in state["validation_feedback"])


def test_match_result_is_clamped_and_contains_evidence():
    result = build_match_result(
        {
            "total_score": 70,
            "hard_score": 60,
            "soft_score": 80,
            "exp_score": 70,
            "matched_skills": ["Java"],
            "missing_skills": ["Kafka"],
        },
        {
            "total_score": 120,
            "matched_skills": ["Java", "未提供的技能"],
            "missing_skills": [],
            "summary": "匹配度较高",
        },
    )

    assert result.total_score == 100
    assert result.matched_skills == ["Java"]
    assert result.missing_skills == ["Kafka"]
    assert result.evidence
    assert {item.field for item in result.evidence} == {"matched_skills", "missing_skills"}


def test_resume_optimize_graph_compiles_with_conditional_routes():
    graph = build_resume_optimize_graph()

    assert graph is not None
