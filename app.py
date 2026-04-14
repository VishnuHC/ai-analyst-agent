import streamlit as st
from main import init_system, handle_query
import os
import io
import sys

# --- Page Config ---
st.set_page_config(page_title="AI Analyst Agent", layout="wide")

st.title("🤖 AI Analyst Agent")
st.markdown("Ask questions about your data, documents, or images.")

# --- Initialize System Once ---
if "initialized" not in st.session_state:
    try:
        init_system()
        st.session_state.initialized = True
    except Exception as e:
        st.error(f"Initialization error: {e}")

col1, col2 = st.columns(2)

with col1:
    st.markdown("## 📂 Upload Data")

    uploaded_files = st.file_uploader(
        "Upload CSV, Excel, Images, or PDFs",
        type=["csv", "xlsx", "png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=True
    )

    # Save uploaded files to data/ folder
    if uploaded_files:
        os.makedirs("data", exist_ok=True)

        saved = []
        for file in uploaded_files:
            file_path = os.path.join("data", file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            saved.append(file.name)

        st.success(f"Uploaded: {', '.join(saved)}")

        # Reinitialize system to include new data
        try:
            init_system()
        except Exception as e:
            st.error(f"Re-initialization error: {e}")

        st.rerun()

with col2:
    st.markdown("## 📁 Current Data Files")

    data_folder = "data"
    if os.path.exists(data_folder):
        files = [f for f in os.listdir(data_folder) if not f.startswith(".")]
        if files:
            for f in files:
                st.markdown(f"- {f}")
        else:
            st.info("No files in data folder.")
    else:
        st.info("Data folder not found.")

# Divider before chat
st.markdown("---")

# --- Session State ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Input Box ---
query = st.text_input("Ask a question:")

# --- Run Button ---
if st.button("Run") and query:
    log_placeholder = st.empty()
    logs = []

    def log(msg):
        logs.append(msg)
        log_placeholder.code("\n".join(logs))

    log("🚀 Starting analysis...")
    log(f"📥 Query: {query}")

    with st.spinner("Analyzing..."):
        try:
            log("⚙️ Running agent pipeline...")

            # Capture backend logs
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            result = handle_query(query)

            backend_logs = sys.stdout.getvalue()
            sys.stdout = old_stdout

            # Display backend logs
            if backend_logs:
                log("📜 Backend Logs:")
                for line in backend_logs.split("\n"):
                    if line.strip():
                        log(line)

            log("✅ Agent execution completed")

            # Handle both dict and string outputs
            if isinstance(result, dict):
                response = result.get("explanation", str(result))
            else:
                response = str(result)

            log("🧠 Processing response...")
        except Exception as e:
            response = f"Error: {e}"

        st.session_state.history.append((query, response))
        log("📊 Output ready")

st.markdown("## 📊 Insights (Preview)")
st.info("Charts and tables will appear here when available.")

# --- Display Chat History ---
st.markdown("## Conversation")

for q, r in reversed(st.session_state.history):
    st.markdown(f"### 🧑 You")
    st.info(q)

    st.markdown(f"### 🤖 AI")
    st.success(r)

    # Download button
    st.download_button(
        label="Download Response",
        data=r,
        file_name="analysis.txt",
        mime="text/plain",
        key=f"download_{q}_{r[:10]}"
    )

    st.markdown("---")