import os
from typing import List, Optional

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None




class EmbeddingEngine:
    """
    Offline-first embedding engine.
    - Loads a local SentenceTransformer model
    - Falls back gracefully if not available
    - Provides a simple encode() API
    """

    def __init__(
        self,
        model_name: str = "all-mpnet-base-v2",
        local_path: Optional[str] = None,
        device: Optional[str] = None,
        available_models: Optional[dict] = None,
    ):
        self.model_name = model_name
        self.local_path = local_path
        self.device = device
        # Model registry for switching
        self.available_models = available_models or {
            "mini": "all-MiniLM-L6-v2",
            "fast": "all-MiniLM-L6-v2",
            "accurate": "all-mpnet-base-v2"
        }
        self.model = None
        self._load_model()

    def _load_model(self):
        """
        Load model strictly from local files.
        Priority:
        1) explicit local_path
        2) cached model_name (local_files_only=True)
        """
        if SentenceTransformer is None:
            print("⚠️ sentence-transformers not installed. Embeddings disabled.")
            self.model = None
            return

        try:
            if self.local_path and os.path.isdir(self.local_path):
                self.model = SentenceTransformer(self.local_path, device=self.device)
                print(f"✔ Embedding model loaded from local path: {self.local_path}")
            else:
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    cache_folder=None,
                    local_files_only=True,
                )
                print(f"✔ Embedding model loaded locally: {self.model_name}")
        except Exception as e:
            print("⚠️ Failed to load embedding model locally.")
            print("Reason:", e)
            print("→ EmbeddingEngine will run in fallback (keyword) mode.")
            self.model = None

    def switch_model(self, model_key: str):
        """
        Disabled: model switching breaks embedding consistency.
        """
        print("⚠️ Model switching disabled to maintain embedding consistency.")

    def is_available(self) -> bool:
        return self.model is not None

    def encode(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        Encode a list of texts into embeddings.
        Returns np.ndarray of shape (n, d) or None if unavailable.
        """
        if not self.model:
            return None
        if isinstance(texts, str):
            texts = [texts]
        emb = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return emb.astype("float32")

    # --------- Simple keyword fallback (no embeddings) ---------
    @staticmethod
    def keyword_match(query: str, chunks: List[str], top_k: int = 5) -> List[int]:
        """
        Very simple scoring: count overlapping tokens.
        Returns indices of top_k chunks.
        """
        q_tokens = set(query.lower().split())
        scores = []
        for i, ch in enumerate(chunks):
            c_tokens = set(ch.lower().split())
            score = len(q_tokens & c_tokens)
            scores.append((score, i))
        scores.sort(reverse=True)
        return [i for _, i in scores[:top_k]]
    def info(self):
        """
        Return current model info
        """
        return {
            "model_name": self.model_name,
            "available": self.is_available(),
            "device": self.device
        }