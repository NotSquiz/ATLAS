"""
ATLAS Embeddings Module

BGE-small-en-v1.5 embeddings via sentence-transformers ONNX backend.
384-dimension embeddings optimized for CPU inference.

Usage:
    from atlas.memory.embeddings import get_embedder

    embedder = get_embedder()
    result = embedder.embed("User prefers morning workouts")
    print(result.embedding)  # 384-dim vector
    print(result.duration_ms)  # ~10-15ms
"""

import time
from dataclasses import dataclass
from typing import Optional

# Lazy imports to avoid loading heavy dependencies at module import
_SentenceTransformer = None


def _get_sentence_transformer():
    """Lazy import sentence_transformers."""
    global _SentenceTransformer
    if _SentenceTransformer is None:
        from sentence_transformers import SentenceTransformer
        _SentenceTransformer = SentenceTransformer
    return _SentenceTransformer


@dataclass
class EmbeddingResult:
    """Result from embedding generation."""
    embedding: list[float]
    duration_ms: float
    text_length: int


class BGEEmbedder:
    """
    BGE-small-en-v1.5 embeddings via sentence-transformers ONNX.

    Uses ONNX backend for efficient CPU inference.
    384 dimensions, ~10-15ms per embedding.

    Usage:
        embedder = BGEEmbedder()

        # Single text
        result = embedder.embed("workout preferences")
        print(result.embedding)  # 384-dim vector

        # Batch
        embeddings = embedder.embed_batch(["text1", "text2"])

        # Query with instruction prefix (for retrieval)
        query_embedding = embedder.embed_query("best workout routine")
    """

    MODEL_NAME = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM = 384
    QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

    def __init__(self, device: str = "cpu"):
        """
        Initialize BGE embedder.

        Args:
            device: Device to run on ('cpu' recommended to preserve GPU for LLM/TTS)
        """
        self.device = device
        self._model = None

    def _ensure_loaded(self) -> None:
        """Lazy-load model on first use."""
        if self._model is not None:
            return

        SentenceTransformer = _get_sentence_transformer()

        # Load with ONNX backend for efficiency
        self._model = SentenceTransformer(
            self.MODEL_NAME,
            device=self.device,
            backend="onnx",
        )

    def embed(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult with 384-dim embedding and timing info
        """
        self._ensure_loaded()

        start = time.perf_counter()
        embedding = self._model.encode(text, normalize_embeddings=True)
        duration_ms = (time.perf_counter() - start) * 1000

        return EmbeddingResult(
            embedding=embedding.tolist(),
            duration_ms=duration_ms,
            text_length=len(text),
        )

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of 384-dim embeddings
        """
        self._ensure_loaded()

        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for search query with instruction prefix.

        BGE models perform better when queries include an instruction
        prefix for retrieval tasks.

        Args:
            query: Search query text

        Returns:
            384-dim embedding optimized for retrieval
        """
        prefixed = f"{self.QUERY_INSTRUCTION}{query}"
        return self.embed(prefixed).embedding

    def is_available(self) -> bool:
        """Check if sentence-transformers is available."""
        try:
            _get_sentence_transformer()
            return True
        except ImportError:
            return False

    @property
    def embedding_dim(self) -> int:
        """Return embedding dimension (384)."""
        return self.EMBEDDING_DIM


# Singleton instance
_embedder: Optional[BGEEmbedder] = None


def get_embedder() -> BGEEmbedder:
    """
    Get singleton embedder instance.

    Returns:
        BGEEmbedder configured for CPU inference
    """
    global _embedder
    if _embedder is None:
        _embedder = BGEEmbedder()
    return _embedder
