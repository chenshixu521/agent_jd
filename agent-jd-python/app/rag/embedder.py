import hashlib

import numpy as np


class HashEmbedder:
    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            vec = np.zeros(self.dim, dtype="float32")
            for token in self._tokens(text):
                digest = hashlib.md5(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "little") % self.dim
                vec[index] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
        return np.vstack(vectors).astype("float32")

    def _tokens(self, text: str) -> list[str]:
        raw = text.replace("，", " ").replace("。", " ").replace(",", " ").replace(".", " ")
        return [item.strip().lower() for item in raw.split() if item.strip()]
