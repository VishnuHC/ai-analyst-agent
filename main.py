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

def init_system():
    """
    Initialize RAG, clean processed data, and sync datasets.
    Safe to call multiple times.
    """
    # Load documents into RAG system
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

    print(f"[Init] RAG loaded with {unique_count} unique document(s).")

    # Clean processed data
    processed_folder = "processed_data"
    if os.path.exists(processed_folder):
        print("[Cleaning]: Removing old processed data...")
        shutil.rmtree(processed_folder)
        os.makedirs(processed_folder, exist_ok=True)

    # Sync datasets
    catalog = sync_catalog_with_data("data")

    for file_name, meta in catalog.items():
        if meta.get("needs_analysis"):
            try:
                file_path = os.path.join("data", file_name)
                print(f"[Auto-Analyzing]: {file_name}")

                df = load_file(file_path)
                df_clean, _ = clean_data(df, file_name)

                profile = profile_data(df_clean)
                save_metadata(file_name, profile)
                update_dataset_catalog(file_name, profile)

                print(f"[Analysis Complete]: {file_name}")

            except Exception as e:
                print(f"[Analysis Failed]: {file_name} → {e}")

def handle_query(query: str):
    """
    Unified query handler for CLI + UI.
    """
    if query.strip().lower() == "/clear":
        print("\n[Resetting System]")

        if os.path.exists("llm_cache.json"):
            os.remove("llm_cache.json")

        if os.path.exists("data_catalog.json"):
            os.remove("data_catalog.json")

        processed_folder = "processed_data"
        if os.path.exists(processed_folder):
            shutil.rmtree(processed_folder)
            os.makedirs(processed_folder, exist_ok=True)

        rag_engine.index = None
        rag_engine.chunks_store = []
        rag_engine.sources_store = []

        init_system()

        return "System reset complete."

    if query.lower() in ["exit", "quit"]:
        return "exit"

    try:
        return run_agent(query)
    except Exception as e:
        return f"[Agent Error]: {e}"

if __name__ == "__main__":
    init_system()

    print("AI Data Agent Ready (type 'exit' to quit)\n")

    while True:
        try:
            query = input("Ask a question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not query:
            continue

        start_time = time.time()
        result = handle_query(query)
        end_time = time.time()

        if isinstance(result, dict):
            print("\nComputed Result:")
            print(result.get("result"))

            print("\nAI Explanation:")
            print(result.get("explanation"))
        else:
            print("\nAgent Response:")
            print(result)

        print(f"\n[Execution Time]: {round(end_time - start_time, 2)} seconds")