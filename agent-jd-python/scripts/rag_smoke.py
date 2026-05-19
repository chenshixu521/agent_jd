import asyncio

from app.rag.service import RagService


async def main() -> None:
    service = RagService()
    hits = await service.asearch_multi("Java LangGraph RAG Agent 项目", ["jd", "project_template", "skill_keyword"], top_k=5)
    for hit in hits:
        print(f"{hit.kb} | {hit.doc_id} | {hit.score:.4f} | {hit.text[:80]}")
    print(await service.abuild_prompt_context("Java LangGraph RAG Agent 项目", ["jd", "project_template", "skill_keyword"], top_k=3))


if __name__ == "__main__":
    asyncio.run(main())
