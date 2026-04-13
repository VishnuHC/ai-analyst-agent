import numpy as np
import faiss
from embedding_engine import EmbeddingEngine

# Initialize embedding engine (offline-first)
embedding_engine = EmbeddingEngine()

index = None
chunks_store = []
sources_store = []  # will store (filename, page_number)


def chunk_text(text, chunk_size=150, overlap=50):
    """
    Split text into overlapping chunks for better context retrieval
    """
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += (chunk_size - overlap)

    return chunks


def add_document(text, filename="unknown", page_number=None):
    """
    Add document to FAISS index
    """
    print(f"[RAG] Adding document: {filename}")
    global index, chunks_store, sources_store

    chunks = chunk_text(text)

    # Encode chunks using embedding engine
    embs = embedding_engine.encode(chunks)

    # Fallback: if embeddings unavailable, just store chunks (no FAISS)
    if embs is None:
        for chunk in chunks:
            chunks_store.append(chunk)
            sources_store.append((filename, page_number))
        return

    embeddings = []
    for i, chunk in enumerate(chunks):
        embeddings.append(embs[i])
        chunks_store.append(chunk)
        sources_store.append((filename, page_number))

    embeddings = np.array(embeddings).astype("float32")

    if index is None:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)

    index.add(embeddings)


def add_dataframe(df, filename="unknown"):
    """
    Convert DataFrame (including OCR text DF) into text and add to RAG.
    """
    try:
        # If OCR text column exists, prioritize it
        if "text" in df.columns:
            text = "\n".join(df["text"].astype(str).tolist())
        else:
            # fallback: convert entire DF to string
            text = df.to_string(index=False)
        
        add_document(text, filename=filename)
    
    except Exception as e:
        print(f"[RAG DF Error]: {e}")


def retrieve(query, top_k=5):
    """
    Retrieve most relevant chunks using FAISS
    """
    global index, chunks_store, sources_store

    if index is None or len(chunks_store) == 0:
        return []

    query_embs = embedding_engine.encode([query])

    # Fallback: keyword-based retrieval if embeddings unavailable
    if query_embs is None:
        idxs = embedding_engine.keyword_match(query, chunks_store, top_k=top_k)
        results = []
        for idx in idxs:
            filename, page = sources_store[idx]
            chunk = chunks_store[idx]
            source_str = f"{filename}, Page {page}" if page is not None else filename
            results.append(f"[Source: {source_str}] {chunk[:500]}")
        return results

    query_emb = query_embs[0].reshape(1, -1)

    distances, indices = index.search(query_emb, top_k)

    results = []
    seen = set()

    for idx in indices[0]:
        if idx < len(chunks_store):
            filename, page = sources_store[idx]
            chunk = chunks_store[idx]

            # avoid duplicate chunks
            if chunk in seen:
                continue
            seen.add(chunk)

            if page is not None:
                source_str = f"{filename}, Page {page}"
            else:
                source_str = filename

            # trim long chunks for better prompt usage
            trimmed_chunk = chunk[:400].strip()

            results.append(f"[Source: {source_str}] {trimmed_chunk}")

    return results