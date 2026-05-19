from fastapi import APIRouter, Depends

from app.api.deps import bind_context
from app.api.schemas.common import AgentResponse
from app.api.schemas.rag import KnowledgeDocIn, RagIndexRequest, RagSearchRequest
from app.core.security import verify_internal_token
from app.core.tracing import get_trace_id
from app.rag.schema import KnowledgeDoc
from app.rag.service import get_rag_service

router = APIRouter(prefix="/rag", dependencies=[Depends(bind_context), Depends(verify_internal_token)])


@router.post("/index", response_model=AgentResponse)
async def index(request: RagIndexRequest) -> AgentResponse:
    docs = [_to_doc(item) for item in request.docs]
    result = await get_rag_service().aadd_documents(docs, chunk_size=request.chunk_size, overlap=request.overlap)
    return AgentResponse(data={"indexed": result}, traceId=get_trace_id())


@router.post("/search", response_model=AgentResponse)
async def search(request: RagSearchRequest) -> AgentResponse:
    hits = await get_rag_service().asearch_multi(request.query, request.kbs, top_k=request.top_k, filters=request.filters)
    return AgentResponse(data={"hits": [hit.__dict__ for hit in hits]}, traceId=get_trace_id())


@router.post("/prompt-context", response_model=AgentResponse)
async def prompt_context(request: RagSearchRequest) -> AgentResponse:
    context = await get_rag_service().abuild_prompt_context(request.query, request.kbs, top_k=request.top_k)
    return AgentResponse(data={"context": context}, traceId=get_trace_id())


def _to_doc(item: KnowledgeDocIn) -> KnowledgeDoc:
    return KnowledgeDoc(kb=item.kb, doc_id=item.doc_id, text=item.text, metadata=item.metadata)
