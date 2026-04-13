

import re
from typing import Dict, List


# --- Synonym dictionary (expandable) ---
SYNONYMS: Dict[str, List[str]] = {
    "sales": ["revenue", "turnover", "income"],
    "profit": ["earnings", "net income"],
    "cost": ["expense", "spend", "expenditure"],
    "trend": ["pattern", "movement"],
    "compare": ["difference", "contrast"],
    "analyze": ["analysis", "evaluate", "study"],
}


# --- Noise words to remove ---
STOPWORDS = {
    "please", "hey", "hi", "can", "you", "tell", "me", "about",
    "the", "a", "an", "bro", "pls", "kindly"
}


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _remove_stopwords(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t not in STOPWORDS]


def _map_synonyms(tokens: List[str]) -> List[str]:
    mapped = []
    for token in tokens:
        replaced = False
        for canonical, variants in SYNONYMS.items():
            if token == canonical or token in variants:
                mapped.append(canonical)
                replaced = True
                break
        if not replaced:
            mapped.append(token)
    return mapped


def normalize_query(query: str) -> str:
    """
    Main function:
    - clean query
    - remove noise
    - map synonyms
    - return normalized query
    """
    text = _normalize_text(query)
    tokens = text.split()

    tokens = _remove_stopwords(tokens)
    tokens = _map_synonyms(tokens)

    return " ".join(tokens)


# --- Simple intent enhancement ---
def enhance_query(query: str) -> str:
    """
    Add implicit intent if missing
    """
    q = normalize_query(query)

    # If no clear action word, assume analysis
    if not any(k in q for k in ["analyze", "compare", "trend"]):
        q = "analyze " + q

    return q


# --- Context memory (simple) ---
class QueryContext:
    def __init__(self):
        self.history: List[str] = []

    def add(self, query: str):
        self.history.append(query)

    def get_last(self) -> str:
        return self.history[-1] if self.history else ""

    def get_contextual_query(self, query: str) -> str:
        """
        If query is vague, enrich using last query
        """
        if len(query.split()) < 3 and self.history:
            return self.history[-1] + " " + query
        return query