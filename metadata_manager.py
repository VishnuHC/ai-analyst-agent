import json
import os

def save_metadata(file_name, profile):
    os.makedirs("metadata", exist_ok=True)

    file_name = file_name.replace(".", "_")
    path = f"metadata/{file_name}.json"

    with open(path, "w") as f:
        json.dump(profile, f, indent=4)