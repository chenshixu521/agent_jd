from app.memory.schema import ChatMessage


class ContextWindowPolicy:
    def __init__(self, max_tokens: int = 4000, reserve_tokens: int = 800, max_messages: int = 30):
        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens
        self.max_messages = max_messages

    @property
    def available_tokens(self) -> int:
        return max(1, self.max_tokens - self.reserve_tokens)

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        ascii_words = len([item for item in text.split() if item.strip()])
        cjk_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
        non_space_chars = len([char for char in text if not char.isspace()])
        return max(ascii_words + cjk_chars, non_space_chars // 4, 1)

    def trim(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        budget = self.available_tokens
        selected: list[ChatMessage] = []
        used = 0
        for message in reversed(messages[-self.max_messages:]):
            cost = self.count_tokens(message.content)
            if selected and used + cost > budget:
                break
            if not selected and cost > budget:
                selected.append(self._truncate_message(message, budget))
                break
            selected.append(message)
            used += cost
        return list(reversed(selected))

    def _truncate_message(self, message: ChatMessage, budget: int) -> ChatMessage:
        keep_chars = max(50, budget * 4)
        return ChatMessage(
            role=message.role,
            content=message.content[-keep_chars:],
            message_id=message.message_id,
            created_at=message.created_at,
            metadata={**message.metadata, "trimmed": True},
        )
