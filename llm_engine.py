import requests

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