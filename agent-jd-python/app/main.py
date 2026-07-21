from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1 import api_router
from app.core.errors import AgentError, agent_error_handler, unhandled_error_handler
from app.core.logger import setup_logging
from app.core.settings import settings

setup_logging()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(AgentError, agent_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)
app.include_router(api_router)


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(content=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})
