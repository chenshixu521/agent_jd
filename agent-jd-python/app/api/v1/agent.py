from uuid import uuid4

from fastapi import APIRouter, Depends
from loguru import logger

from app.agents.router import run_agent
from app.api.deps import bind_context
from app.api.schemas.common import AgentRequest, AgentResponse
from app.core.security import verify_internal_token
from app.core.tracing import get_trace_id
from app.infra.redis_client import get_context, set_context, set_task_status

router = APIRouter(dependencies=[Depends(bind_context), Depends(verify_internal_token)])


async def execute(capability: str, action: str, request: AgentRequest) -> AgentResponse:
    task_id = request.task_id or str(uuid4())
    trace_id = get_trace_id()
    cached = await get_context(task_id)
    if (
        cached is not None
        and cached.get("capability") == capability
        and cached.get("action") == action
        and "result" in cached
    ):
        await set_task_status(task_id, "SUCCESS", 100, {"capability": capability, "action": action, "trace_id": trace_id})
        logger.info(f"Agent request cache hit taskId={task_id} capability={capability} action={action} traceId={trace_id}")
        return AgentResponse(taskId=task_id, data=cached["result"], traceId=trace_id)
    logger.info(f"Agent request start taskId={task_id} capability={capability} action={action} traceId={trace_id}")
    await set_task_status(task_id, "RUNNING", 10, {"capability": capability, "action": action, "trace_id": trace_id})
    try:
        data = await run_agent(capability, action, task_id, request.payload)
        await set_context(task_id, {"capability": capability, "action": action, "payload": request.payload, "result": data})
        await set_task_status(task_id, "SUCCESS", 100, {"capability": capability, "action": action, "trace_id": trace_id})
        logger.info(f"Agent request success taskId={task_id} capability={capability} action={action} traceId={trace_id}")
        return AgentResponse(taskId=task_id, data=data, traceId=trace_id)
    except Exception as exc:
        await set_task_status(task_id, "FAILED", 100, {"capability": capability, "action": action, "trace_id": trace_id, "error": str(exc)})
        logger.exception(f"Agent request failed taskId={task_id} capability={capability} action={action} traceId={trace_id}")
        raise


@router.post("/resume/{action}", response_model=AgentResponse)
async def resume(action: str, request: AgentRequest) -> AgentResponse:
    return await execute("resume", action, request)


@router.post("/jd/{action}", response_model=AgentResponse)
async def jd(action: str, request: AgentRequest) -> AgentResponse:
    return await execute("jd", action, request)


@router.post("/keyword/{action}", response_model=AgentResponse)
async def keyword(action: str, request: AgentRequest) -> AgentResponse:
    return await execute("keyword", action, request)


@router.post("/project/{action}", response_model=AgentResponse)
async def project(action: str, request: AgentRequest) -> AgentResponse:
    return await execute("project", action, request)


@router.post("/greeting/{action}", response_model=AgentResponse)
async def greeting(action: str, request: AgentRequest) -> AgentResponse:
    return await execute("greeting", action, request)


@router.post("/match/{action}", response_model=AgentResponse)
async def match(action: str, request: AgentRequest) -> AgentResponse:
    return await execute("match", action, request)


@router.post("/chat/{action}", response_model=AgentResponse)
async def chat(action: str, request: AgentRequest) -> AgentResponse:
    return await execute("chat", action, request)
