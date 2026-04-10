from ingestion import load_file
from profiling import profile_data
from metadata_manager import save_metadata
from cleaning import clean_data
from llm_engine import ask_llm
from agent import run_agent
import os
from dataset_agent import update_dataset_catalog, load_catalog, sync_catalog_with_data
from document_loader import load_documents
from rag_engine import add_document
import shutil
import rag_engine
import time

def autonomous_analysis(interval=60):
    """
    Runs periodic analysis automatically.
    """
    print("\n[Autonomous Mode Activated]")

    while True:
        try:
            catalog = load_catalog()

            for file_name in catalog.keys():
                query = f"Give key business insights for {file_name}"
                print(f"\n[Auto Query]: {query}")

                output = run_agent(query)

                if isinstance(output, dict):
                    print("\n[Auto Result]:")
                    print(output["result"])
                    print("\n[Auto Insights]:")
                    print(output["explanation"])

        except Exception as e:
            print("[Autonomous Error]:", e)

        print(f"\n[Waiting {interval} seconds before next run...]\n")
        time.sleep(interval)

def run_pipeline(file_path):
    file_name = os.path.basename(file_path)

    print(f"\nProcessing: {file_name}")

    df = load_file(file_path)
    df_clean, clean_path = clean_data(df, file_name)
    print("\nCleaned file saved at:", clean_path)

    print("\nLoaded Data:")
    print(df.head())

    profile = profile_data(df_clean)

    save_metadata(file_name, profile)
    update_dataset_catalog(file_name, profile)

    print("\nProfile Summary:")
    print(profile)

    return df_clean, profile


if __name__ == "__main__":
    # Load documents into RAG system (from unified data folder)
    docs = load_documents("data")

    seen_docs = set()
    unique_count = 0

    for doc in docs:
        text, filename, page = doc

        key = (filename, page)
        if key not in seen_docs:
            add_document(text, filename, page)
            seen_docs.add(key)
            unique_count += 1

    print(f"RAG loaded with {unique_count} unique document(s).")

    # --- Clean processed_data if data folder changed ---
    processed_folder = "processed_data"
    if os.path.exists(processed_folder):
        print("[Cleaning]: Removing old processed data...")
        shutil.rmtree(processed_folder)
        os.makedirs(processed_folder, exist_ok=True)

    # --- Sync and auto-analyze datasets in /data ---
    catalog = sync_catalog_with_data("data")

    for file_name, meta in catalog.items():
        if meta.get("needs_analysis"):
            try:
                file_path = os.path.join("data", file_name)
                print(f"\n[Auto-Analyzing]: {file_name}")

                df = load_file(file_path)
                df_clean, _ = clean_data(df, file_name)

                profile = profile_data(df_clean)
                save_metadata(file_name, profile)
                update_dataset_catalog(file_name, profile)

                print(f"[Analysis Complete]: {file_name}")

            except Exception as e:
                print(f"[Analysis Failed]: {file_name} → {e}")

    print("AI Data Agent Ready (type 'exit' to quit)\n")

    while True:
        query = input("Ask a question: ")

        if query.strip().lower() == "/auto":
            autonomous_analysis(60)
            continue

        if query.strip().lower() == "/clear":
            print("\n[Resetting System]")

            # --- Clear cache ---
            if os.path.exists("llm_cache.json"):
                os.remove("llm_cache.json")
                print("Cache cleared.")

            # --- Clear dataset catalog ---
            if os.path.exists("data_catalog.json"):
                os.remove("data_catalog.json")
                print("Dataset catalog cleared.")

            # --- Clear processed data ---
            processed_folder = "processed_data"
            if os.path.exists(processed_folder):
                shutil.rmtree(processed_folder)
                os.makedirs(processed_folder, exist_ok=True)
                print("Processed data cleared.")

            # --- Reset RAG completely ---
            rag_engine.index = None
            rag_engine.chunks_store = []
            rag_engine.sources_store = []
            print("RAG memory cleared.")

            # Reload only current data folder
            docs = load_documents("data")
            seen_docs = set()

            for doc in docs:
                text, filename, page = doc
                key = (filename, page)
                if key not in seen_docs:
                    add_document(text, filename, page)
                    seen_docs.add(key)

            # --- Rebuild dataset catalog after clear ---
            print("Rebuilding dataset catalog...")
            catalog = sync_catalog_with_data("data")

            for file_name, meta in catalog.items():
                if meta.get("needs_analysis"):
                    try:
                        file_path = os.path.join("data", file_name)
                        print(f"[Re-Analyzing]: {file_name}")

                        df = load_file(file_path)
                        df_clean, _ = clean_data(df, file_name)

                        profile = profile_data(df_clean)
                        save_metadata(file_name, profile)
                        update_dataset_catalog(file_name, profile)

                        print(f"[Analysis Complete]: {file_name}")

                    except Exception as e:
                        print(f"[Analysis Failed]: {file_name} → {e}")

            print("System reset complete. Only /data retained.\n")
            continue

        if query.lower() in ["exit", "quit"]:
            break

        agent_output = run_agent(query)

        if isinstance(agent_output, dict):
            print("\nComputed Result:")
            print(agent_output["result"])

            print("\nAI Explanation:")
            print(agent_output["explanation"])
        else:
            print("\nAgent Response:")
            print(agent_output)