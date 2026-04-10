import json
import os

CATALOG_PATH = "metadata/catalog.json"

def load_catalog():
    if not os.path.exists(CATALOG_PATH):
        return {}

    with open(CATALOG_PATH, "r") as f:
        return json.load(f)


def update_catalog(file_name, profile):
    os.makedirs("metadata", exist_ok=True)

    catalog = load_catalog()

    catalog[file_name] = {
        "columns": profile.get("columns", []),
        "dtypes": profile.get("dtypes", {}),
        "num_rows": profile.get("num_rows", 0)
    }

    with open(CATALOG_PATH, "w") as f:
        json.dump(catalog, f, indent=4)


def list_datasets():
    catalog = load_catalog()
    return list(catalog.keys())


def find_dataset_by_column(column_name):
    catalog = load_catalog()

    results = []
    for file, info in catalog.items():
        if column_name in info.get("columns", []):
            results.append(file)

    return results
