from fastapi import APIRouter, Depends

from app.api.deps import bind_context
from app.api.schemas.common import AgentResponse
from app.api.schemas.session import MessageAppendRequest, SessionCreateRequest
from app.core.security import verify_internal_token
from app.core.tracing import get_trace_id
from app.memory.schema import ChatMessage
from app.memory.session_store import get_session_store

router = APIRouter(prefix="/sessions", dependencies=[Depends(bind_context), Depends(verify_internal_token)])


@router.post("", response_model=AgentResponse)
async def create_session(request: SessionCreateRequest) -> AgentResponse:
    state = await get_session_store().create_session(user_id=request.user_id, title=request.title, metadata=request.metadata)
    return AgentResponse(data=state.to_dict(), traceId=get_trace_id())


@router.get("/{session_id}", response_model=AgentResponse)
async def get_session(session_id: str) -> AgentResponse:
    state = await get_session_store().get_session(session_id)
    return AgentResponse(data=state.to_dict() if state else None, traceId=get_trace_id())


@router.post("/{session_id}/messages", response_model=AgentResponse)
async def append_message(session_id: str, request: MessageAppendRequest) -> AgentResponse:
    message = ChatMessage(role=request.role, content=request.content, metadata=request.metadata)
    await get_session_store().append_message(session_id, message)
    return AgentResponse(data=message.to_dict(), traceId=get_trace_id())


@router.get("/{session_id}/messages", response_model=AgentResponse)
async def list_messages(session_id: str, limit: int = 50) -> AgentResponse:
    messages = await get_session_store().list_messages(session_id, limit=limit)
    return AgentResponse(data={"messages": [item.to_dict() for item in messages]}, traceId=get_trace_id())


@router.get("/{session_id}/context", response_model=AgentResponse)
async def context(session_id: str) -> AgentResponse:
    messages = await get_session_store().build_context(session_id)
    return AgentResponse(data={"messages": [item.to_dict() for item in messages]}, traceId=get_trace_id())
