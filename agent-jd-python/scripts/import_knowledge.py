import argparse
import asyncio
import json
from pathlib import Path

from app.rag.schema import KnowledgeDoc
from app.rag.service import RagService


def load_jsonl(path: Path) -> list[KnowledgeDoc]:
    docs: list[KnowledgeDoc] = []
    with path.open("r", encoding="utf-8") as fp:
        for line in fp:
            if not line.strip():
                continue
            item = json.loads(line)
            docs.append(
                KnowledgeDoc(
                    kb=item["kb"],
                    doc_id=item["doc_id"],
                    text=item["text"],
                    metadata=item.get("metadata", {}),
                )
            )
    return docs


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="seed/knowledge.jsonl")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=50)
    args = parser.parse_args()

    docs = load_jsonl(Path(args.file))
    result = await RagService().aadd_documents(docs, chunk_size=args.chunk_size, overlap=args.overlap)
    print(json.dumps({"indexed": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
