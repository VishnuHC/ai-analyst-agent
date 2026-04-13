import requests

import json

def ask_llm(query, data_summary):
    prompt = f"""
You are a business analyst.

User question:
{query}

Data summary:
{data_summary}

Answer clearly and concisely.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]


# ---- LLM Query Interpretation ----

def interpret_query(query: str) -> dict:
    """
    Use LLM to convert a natural query into structured intent.
    Returns a dict with keys: intent, metric, timeframe, filters
    """
    prompt = f"""
You are an AI system that extracts structured intent from user queries.

Return ONLY valid JSON with keys:
- intent (analysis | compare | trend | question)
- metric (e.g., sales, profit, cost, revenue)
- timeframe (e.g., last month, recent, 2024, none)
- filters (list of strings, optional)

User query:
{query}

Example output:
{{
  "intent": "analysis",
  "metric": "sales",
  "timeframe": "recent",
  "filters": []
}}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    text = response.json().get("response", "").strip()

    # Try to extract JSON safely
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except Exception:
        return {
            "intent": "analysis",
            "metric": "",
            "timeframe": "",
            "filters": []
        }


def rewrite_query_from_intent(intent_dict: dict) -> str:
    """
    Convert structured intent back into a clean query string for the agent.
    """
    intent = intent_dict.get("intent", "analysis")
    metric = intent_dict.get("metric", "")
    timeframe = intent_dict.get("timeframe", "")

    parts = [intent]

    if metric:
        parts.append(metric)
    if timeframe and timeframe != "none":
        parts.append(timeframe)

    return " ".join(parts).strip()


def debug_intent(intent_dict: dict):
    print("\n[LLM Intent Parsed]:")
    print(intent_dict)