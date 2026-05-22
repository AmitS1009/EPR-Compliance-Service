import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "do",
    "for",
    "from",
    "greenpack",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "rate",
    "should",
    "the",
    "this",
    "to",
    "what",
    "when",
    "with",
    "year",
}


class LocalTfidfVectorStore:
    """Tiny in-memory vector store for a small, auditable policy corpus."""

    def __init__(self, corpus_path: Path):
        self.corpus_path = corpus_path
        self.documents = self._load_documents()
        self.chunks = self._chunk_documents()
        self.idf = self._build_idf()
        self.vectors = [self._embed(chunk["text"]) for chunk in self.chunks]

    def search(
        self, question: str, top_k: int = 3, min_score: float = 0.12
    ) -> list[dict[str, Any]]:
        query_vector = self._embed(question)
        scored: list[tuple[float, dict[str, Any]]] = []
        for chunk, vector in zip(self.chunks, self.vectors, strict=True):
            score = self._cosine(query_vector, vector)
            if score >= min_score:
                scored.append((score, chunk))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            {
                **chunk,
                "score": round(score, 4),
            }
            for score, chunk in scored[:top_k]
        ]

    def _load_documents(self) -> list[dict[str, Any]]:
        with self.corpus_path.open(encoding="utf-8") as handle:
            return json.load(handle)

    def _chunk_documents(self) -> list[dict[str, str]]:
        chunks: list[dict[str, str]] = []
        for document in self.documents:
            for section in document["sections"]:
                chunks.append(
                    {
                        "document": document["title"],
                        "section": section["heading"],
                        "text": section["text"],
                    }
                )
        return chunks

    def _build_idf(self) -> dict[str, float]:
        doc_count = len(self.chunks)
        document_frequency: Counter[str] = Counter()
        for chunk in self.chunks:
            document_frequency.update(set(self._tokenize(chunk["text"])))
        return {
            token: math.log((1 + doc_count) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }

    def _embed(self, text: str) -> dict[str, float]:
        tokens = self._tokenize(text)
        if not tokens:
            return {}
        counts = Counter(tokens)
        total = len(tokens)
        return {
            token: (count / total) * self.idf.get(token, 1.0)
            for token, count in counts.items()
        }

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [
            token
            for token in TOKEN_RE.findall(text.lower())
            if len(token) > 2 and token not in STOPWORDS
        ]

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        dot = sum(value * right.get(token, 0.0) for token, value in left.items())
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)
