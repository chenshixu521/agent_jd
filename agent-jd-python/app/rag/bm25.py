import math
import re
from collections import Counter


ASCII_TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.\-]*|\d+")
CHINESE_SEQUENCE = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    normalized = (text or "").lower()
    tokens = ASCII_TOKEN.findall(normalized)
    for sequence in CHINESE_SEQUENCE.findall(normalized):
        tokens.extend(sequence)
        tokens.extend(sequence[index : index + 2] for index in range(len(sequence) - 1))
    return [item for item in tokens if item]


class Bm25Index:
    def __init__(self, documents: list[str], k1: float = 1.5, b: float = 0.75):
        self.documents = [tokenize(item) for item in documents]
        self.k1 = k1
        self.b = b
        self.lengths = [len(item) for item in self.documents]
        self.avg_length = sum(self.lengths) / len(self.lengths) if self.lengths else 0.0
        self.term_frequencies = [Counter(item) for item in self.documents]
        self.document_frequency: Counter[str] = Counter()
        for document in self.documents:
            self.document_frequency.update(set(document))

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        query_tokens = tokenize(query)
        if not query_tokens or not self.documents:
            return []
        scores = [(index, self._score(index, query_tokens)) for index in range(len(self.documents))]
        scores = [(index, score) for index, score in scores if score > 0]
        scores.sort(key=lambda item: item[1], reverse=True)
        if not scores:
            return []
        max_score = scores[0][1]
        return [(index, round(score / max_score, 6)) for index, score in scores[:top_k]]

    def _score(self, index: int, query_tokens: list[str]) -> float:
        frequency = self.term_frequencies[index]
        document_length = self.lengths[index]
        score = 0.0
        for token in query_tokens:
            term_frequency = frequency.get(token, 0)
            if term_frequency == 0:
                continue
            doc_frequency = self.document_frequency[token]
            inverse_document_frequency = math.log(
                1 + (len(self.documents) - doc_frequency + 0.5) / (doc_frequency + 0.5)
            )
            length_normalization = term_frequency + self.k1 * (
                1 - self.b + self.b * document_length / max(self.avg_length, 1.0)
            )
            score += inverse_document_frequency * term_frequency * (self.k1 + 1) / length_normalization
        return score
