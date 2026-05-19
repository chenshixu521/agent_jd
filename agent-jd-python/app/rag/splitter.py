from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.schema import KnowledgeDoc, RagChunk


def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    text = " ".join((text or "").split())
    if not text:
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", "。", "，", " ", ""],
    )
    return splitter.split_text(text)


def split_documents(docs: list[KnowledgeDoc], chunk_size: int = 500, overlap: int = 50) -> list[RagChunk]:
    chunks: list[RagChunk] = []
    for doc in docs:
        for index, text in enumerate(split_text(doc.text, chunk_size=chunk_size, overlap=overlap)):
            chunks.append(
                RagChunk(
                    kb=doc.kb,
                    doc_id=doc.doc_id,
                    chunk_id=f"{doc.doc_id}:{index}",
                    text=text,
                    metadata={**doc.metadata, "chunk_index": index},
                )
            )
    return chunks
