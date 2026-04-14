def is_high_quality_chunk(chunk: str) -> bool:
    """
    Dynamically evaluate chunk quality based on:
    - length
    - numeric density
    - information density (unique words)
    - low stopword ratio (less fluff)
    """

    words = chunk.split()
    if len(words) < 30:
        return False

    lower_words = [w.lower() for w in words]

    # --- Numeric density (important for data)
    num_count = sum(1 for c in chunk if c.isdigit())
    numeric_score = num_count / max(len(chunk), 1)

    # --- Unique word ratio (information density)
    unique_ratio = len(set(lower_words)) / len(lower_words)

    # --- Stopword ratio (basic noise detection)
    stopwords = {
        "the", "is", "and", "of", "to", "in", "for", "with",
        "on", "as", "by", "at", "an", "be", "this", "that",
        "from", "or", "it", "are", "was"
    }
    stopword_ratio = sum(1 for w in lower_words if w in stopwords) / len(lower_words)

    # --- Heuristic scoring
    score = (
        (numeric_score * 2.0) +      # prioritize numbers
        (unique_ratio * 1.5) -       # reward information density
        (stopword_ratio * 1.5)       # penalize fluff
    )

    return score > 0.2
import numpy as np
import faiss
from embedding_engine import EmbeddingEngine

# Initialize embedding engine (offline-first)
embedding_engine = EmbeddingEngine()

index = None
chunks_store = []
sources_store = []  # will store (filename, page_number)

# Track already added sources to prevent duplicates
added_sources = set()
# Track unique document names for true document count
document_names = set()


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
    global index, chunks_store, sources_store, added_sources, document_names

    source_key = (filename, page_number)
    if source_key in added_sources:
        return

    print(f"[RAG] Adding document: {filename}")
    added_sources.add(source_key)
    document_names.add(filename)

    chunks = chunk_text(text)

    # Filter chunks for quality
    chunks = [c for c in chunks if is_high_quality_chunk(c)]
    if not chunks:
        return

    # Encode chunks using embedding engine
    embs = embedding_engine.encode(chunks)

    # Fallback: if embeddings unavailable, just store chunks (no FAISS)
    if embs is None:
        for chunk in chunks:
            if chunk not in chunks_store:
                chunks_store.append(chunk)
                sources_store.append((filename, page_number))
        return

    embeddings = []
    for i, chunk in enumerate(chunks):
        embeddings.append(embs[i])
        if chunk not in chunks_store:
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
            if len(trimmed_chunk.split()) < 20:
                continue

            results.append(f"[Source: {source_str}] {trimmed_chunk}")

    return results


# Return the number of unique documents added
def get_document_count():
    return len(document_names)