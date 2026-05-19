from fastapi import APIRouter

from app.api.v1.agent import router as agent_router
from app.api.v1.health import router as health_router
from app.api.v1.rag import router as rag_router
from app.api.v1.session import router as session_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(health_router)
api_router.include_router(agent_router)
api_router.include_router(rag_router)
api_router.include_router(session_router)
