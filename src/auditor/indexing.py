import math
import re
import hashlib
from collections import Counter
from .models import CodeChunk


def tokens(value: str) -> list[str]:
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]{1,}", value.lower())


class HybridIndex:
    """Small local hybrid retrieval index; embedding backend is intentionally pluggable."""
    def __init__(self, chunks: list[CodeChunk]):
        self.chunks = chunks
        self.docs = [Counter(tokens(c.content + " " + c.name)) for c in chunks]
        self.df = Counter(term for doc in self.docs for term in doc)

    def search(self, query: str, limit: int = 5) -> list[CodeChunk]:
        query_terms = tokens(query)
        scores = []
        count = max(len(self.docs), 1)
        for chunk, doc in zip(self.chunks, self.docs):
            score = sum((1 + math.log(doc[t])) * math.log((count + 1) / (self.df[t] + 1)) for t in query_terms if t in doc)
            scores.append((score, chunk))
        return [chunk for score, chunk in sorted(scores, key=lambda item: item[0], reverse=True)[:limit] if score > 0]


class LocalVectorStore:
    """Chroma-backed persistent store with a deterministic offline embedding fallback."""
    def __init__(self, directory: str, collection_name: str):
        self.directory, self.collection_name = directory, collection_name

    @staticmethod
    def _offline_embedding(text: str, dimensions: int = 128) -> list[float]:
        vector = [0.0] * dimensions
        for token in tokens(text):
            vector[int(hashlib.sha256(token.encode()).hexdigest(), 16) % dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def persist(self, chunks: list[CodeChunk]) -> bool:
        """Persist metadata to Chroma if installed; return False when unavailable."""
        try:
            import chromadb
            client = chromadb.PersistentClient(path=self.directory)
            collection = client.get_or_create_collection(self.collection_name, embedding_function=None)
            collection.upsert(ids=[c.id for c in chunks], documents=[c.content for c in chunks], embeddings=[self._offline_embedding(c.content) for c in chunks], metadatas=[{"file_path": c.file_path, "start_line": c.start_line, "end_line": c.end_line, "name": c.name} for c in chunks])
            return True
        except ImportError:
            return False
