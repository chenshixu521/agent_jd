from app.rag.schema import RagHit


class PromptEnhancer:
    def build_context(self, query: str, hits: list[RagHit]) -> str:
        if not hits:
            return "【RAG检索上下文】\n暂无可用知识库上下文。\n"
        lines = ["【RAG检索上下文】", f"用户查询：{query}", ""]
        for index, hit in enumerate(hits, start=1):
            lines.append(f"[{index}] 知识库: {hit.kb} | 文档: {hit.doc_id} | 相似度: {hit.score:.4f}")
            lines.append(hit.text)
            if hit.metadata:
                lines.append(f"元数据: {hit.metadata}")
            lines.append("")
        lines.append("请仅将以上内容作为参考，不得编造用户未提供的经历。")
        return "\n".join(lines)

    def enhance_messages(self, messages: list[dict[str, str]], query: str, hits: list[RagHit]) -> list[dict[str, str]]:
        context = self.build_context(query, hits)
        enhanced = list(messages)
        enhanced.insert(1 if enhanced and enhanced[0].get("role") == "system" else 0, {"role": "system", "content": context})
        return enhanced
