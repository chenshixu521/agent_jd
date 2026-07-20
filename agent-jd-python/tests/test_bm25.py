from app.rag.bm25 import Bm25Index, tokenize


def test_tokenize_supports_chinese_bigrams_and_technical_terms():
    tokens = tokenize("熟悉 Spring Boot 与分布式系统")

    assert "spring" in tokens
    assert "boot" in tokens
    assert "分布" in tokens


def test_bm25_prefers_matching_document():
    index = Bm25Index(["Java Spring Boot Redis", "Python FastAPI LangGraph"])

    results = index.search("LangGraph Agent", top_k=2)

    assert results[0][0] == 1
