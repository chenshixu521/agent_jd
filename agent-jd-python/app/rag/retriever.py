from app.rag.schema import RagHit
from app.rag.service import get_rag_service


def retrieve_examples(index_name: str, query: str, top_k: int = 3) -> list[str]:
    kb = _legacy_index_to_kb(index_name)
    return [item.text for item in get_rag_service().search(query, kb=kb, top_k=top_k)]


def retrieve_hits(kbs: list[str], query: str, top_k: int = 5) -> list[RagHit]:
    return get_rag_service().search_multi(query, kbs=kbs, top_k=top_k)


async def aretrieve_hits(kbs: list[str], query: str, top_k: int = 5) -> list[RagHit]:
    return await get_rag_service().asearch_multi(query, kbs=kbs, top_k=top_k)


def build_prompt_context(kbs: list[str], query: str, top_k: int = 5) -> str:
    return get_rag_service().build_prompt_context(query, kbs=kbs, top_k=top_k)


async def abuild_prompt_context(kbs: list[str], query: str, top_k: int = 5) -> str:
    return await get_rag_service().abuild_prompt_context(query, kbs=kbs, top_k=top_k)


def _legacy_index_to_kb(index_name: str) -> str:
    mapping = {
        "resume_corpus": "resume_corpus",
        "project_corpus": "project_template",
        "jd_corpus": "jd",
        "skill_taxonomy": "skill_keyword",
    }
    return mapping.get(index_name, index_name)
