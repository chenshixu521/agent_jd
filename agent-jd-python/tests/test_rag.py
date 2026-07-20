from pathlib import Path

from app.rag.embedding_api import HashEmbeddingProvider
from app.rag.schema import KnowledgeDoc
from app.rag.service import RagService


def test_rag_service_indexes_and_searches_multiple_knowledge_bases(tmp_path: Path):
    service = RagService(root=tmp_path, embedder=HashEmbeddingProvider())
    service.add_documents([
        KnowledgeDoc(kb="jd", doc_id="jd-java-1", text="Java 后端岗位要求 Spring Boot、MySQL、Redis 和微服务经验", metadata={"role": "java"}),
        KnowledgeDoc(kb="project_template", doc_id="tpl-agent-1", text="AI Agent 项目模板：LangGraph 工作流、RAG 检索、工具调用和结果聚合", metadata={"scene": "agent"}),
    ])

    hits = service.search_multi("LangGraph RAG Agent 项目", kbs=["project_template", "jd"], top_k=3)

    assert hits
    assert hits[0].kb in {"project_template", "jd"}
    assert any("LangGraph" in item.text for item in hits)


def test_rag_service_builds_prompt_context(tmp_path: Path):
    service = RagService(root=tmp_path, embedder=HashEmbeddingProvider())
    service.add_documents([
        KnowledgeDoc(kb="greeting_template", doc_id="greet-1", text="您好，我关注到贵司岗位，我的项目经验与岗位要求匹配", metadata={"channel": "boss"}),
    ])

    context = service.build_prompt_context("打招呼", kbs=["greeting_template"], top_k=2)

    assert "【RAG检索上下文】" in context
    assert "greeting_template" in context
    assert "打招呼" in context or "岗位" in context


def test_rag_replaces_existing_document_instead_of_duplicating_it(tmp_path: Path):
    service = RagService(root=tmp_path, embedder=HashEmbeddingProvider())
    service.add_documents([KnowledgeDoc(kb="jd", doc_id="same-doc", text="Java Redis")])
    service.add_documents([KnowledgeDoc(kb="jd", doc_id="same-doc", text="Python FastAPI")])

    hits = service.search_multi("Python FastAPI", kbs=["jd"], top_k=5)

    assert len([item for item in hits if item.doc_id == "same-doc"]) == 1
    assert hits[0].text == "Python FastAPI"
