from llm_engine import ask_llm
import json
import os
import hashlib


CATALOG_PATH = "data_catalog.json"


def load_catalog():
    if not os.path.exists(CATALOG_PATH):
        return {}

    with open(CATALOG_PATH, "r") as f:
        catalog = json.load(f)

    # Auto-sync with actual data folder
    catalog = sync_catalog_with_data()

    return catalog


def save_catalog(catalog):
    with open(CATALOG_PATH, "w") as f:
        json.dump(catalog, f, indent=2)


def get_file_hash(path):
    """
    Generate hash for file to detect changes
    """
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


# --- Sync with data folder ---
def sync_catalog_with_data(folder="data"):
    """
    Sync catalog with actual files in data folder.
    - Removes deleted files
    - Keeps only existing datasets
    """
    # Fix recursion: avoid calling load_catalog() which calls sync_catalog_with_data()
    if not os.path.exists(CATALOG_PATH):
        catalog = {}
    else:
        with open(CATALOG_PATH, "r") as f:
            catalog = json.load(f)

    if not os.path.exists(folder):
        return {}

    actual_files = {
        f: get_file_hash(os.path.join(folder, f))
        for f in os.listdir(folder)
        if f.endswith(".csv") or f.endswith(".xlsx")
    }

    updated_catalog = {}

    for file, file_hash in actual_files.items():
        if file in catalog:
            # check if file changed
            if catalog[file].get("file_hash") == file_hash:
                updated_catalog[file] = catalog[file]
            else:
                print(f"[Dataset Changed]: {file} → re-analysis required")
        else:
            print(f"[New Dataset Detected]: {file}")

    for file, file_hash in actual_files.items():
        if file not in updated_catalog:
            updated_catalog[file] = {
                "columns": [],
                "dtypes": {},
                "num_rows": 0,
                "description": "Pending analysis",
                "use_cases": [],
                "important_columns": [],
                "semantic_tags": [],
                "potential_joins": [],
                "file_hash": file_hash,
                "needs_analysis": True
            }

    save_catalog(updated_catalog)

    return updated_catalog


def analyze_dataset(file_name, profile):
    """
    Uses LLM to understand dataset meaning and use cases
    """

    prompt = f"""
You are a senior business data analyst.

Dataset: {file_name}

Columns: {profile['columns']}
Types: {profile['dtypes']}

TASK:
Understand this dataset in a BUSINESS context.

Return STRICT JSON:

{{
    "description": "what this dataset represents in business terms",
    "use_cases": ["business questions this dataset can answer"],
    "important_columns": ["columns that matter most"],
    "semantic_tags": ["sales", "inventory", "finance", "hr", etc"],
    "potential_joins": ["possible keys like branch_id, product_id, date"]
}}

IMPORTANT:
- Think in business terms, not technical
- Identify how this dataset can connect with others
"""

    response = ask_llm(prompt, "").strip()

    try:
        parsed = json.loads(response)
    except:
        parsed = {
            "description": "Unknown dataset",
            "use_cases": [],
            "important_columns": profile["columns"],
            "semantic_tags": [],
            "potential_joins": []
        }

    return parsed


def update_dataset_catalog(file_name, profile):
    """
    Run this after profiling to enrich dataset metadata
    """

    catalog = load_catalog()

    analysis = analyze_dataset(file_name, profile)

    file_path = os.path.join("data", file_name)
    file_hash = get_file_hash(file_path)

    catalog[file_name] = {
        "columns": profile["columns"],
        "dtypes": profile["dtypes"],
        "num_rows": profile["num_rows"],
        "description": analysis.get("description", ""),
        "use_cases": analysis.get("use_cases", []),
        "important_columns": analysis.get("important_columns", []),
        "semantic_tags": analysis.get("semantic_tags", []),
        "potential_joins": analysis.get("potential_joins", []),
        "file_hash": file_hash,
        "needs_analysis": False
    }

    save_catalog(catalog)

    print(f"\n[Dataset Catalog Updated for {file_name}]")

    return catalog