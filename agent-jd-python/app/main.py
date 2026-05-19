from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
