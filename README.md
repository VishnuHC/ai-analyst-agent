#🧠 AI Analyst Agent

An intelligent, autonomous AI system that performs business data analysis using **RAG (Retrieval-Augmented Generation)**, **multi-agent reasoning**, and **execution pipelines**.

---

## 🚀 Overview

  AI Analyst Agent is designed to act like a **data analyst**, not just a tool.

It can:
- Understand datasets automatically  
- Retrieve insights from documents (PDFs, OCR)  
- Perform multi-dataset analysis  
- Generate reasoning + code + results  
- Learn from past mistakes  
- Run autonomously  

---

## 🔥 Key Features

  🧠 Intelligent Reasoning
    - Intent detection (analysis, comparison, trend, diagnostic)
    - Strategy-based execution planning
    - Structured reasoning pipeline

  📊 Data Intelligence
    - Automatic dataset understanding
    - Semantic tagging & metadata catalog
    - Smart dataset selection (no manual input)
    - Cross-dataset reasoning

  🔗 Advanced Data Handling
    - Intelligent joins across datasets
    - Supports CSV, Excel, PDFs, images
    - OCR pipeline for document extraction

  🔍 RAG (Retrieval-Augmented Generation)
    - Context-aware document retrieval
    - Source tracking (file + page)
    - Hybrid analysis (data + documents)

  ⚙️ Execution Engine
    - Auto-generates Python code
    - Executes analysis dynamically
    - Self-evaluation of outputs

  🔁 Self-Learning System
    - Stores failed cases
    - Improves reasoning over time
    - Reduces repeated errors

  ⚡ Autonomous Mode
    - Runs analysis automatically
    - Generates insights continuously
    - Simulates real analyst behavior

---

## 🏗️ Architecture
  User Query
    → Intent Detection
    → Strategy Selection
    → Dataset Selection
    → RAG Retrieval
    → Reasoning
    → Code Generation
    → Execution
    → Evaluation
    → Memory Update

  ⚙️ Tech Stack
    - Python  
    - Pandas / NumPy  
    - Ollama (Local LLM)  
    - Sentence Transformers (Embeddings)  
    - FAISS (planned)  
    - OCR (Tesseract / EasyOCR)  

🧪 Example Queries
  compare sales across branches
  why did revenue decline
  sales trend over time
  generate business insights

---

## 🛠️ Installation

        git clone https://github.com/VishnnHC/ai-analyst-agent.git
        cd ai-analyst-agent
        pip install -r requirements.txt

🤖 Run Locally

  Make sure you have Ollama installed and running:
  
      ollama pull llama3
      
  Then run:

      python main.py
      
⚡ Autonomous Mode

      /auto
  Runs continuous analysis on available datasets.

---

## 📁 Project Structure

    ai-analyst-agent/
    ├── agent.py
    ├── rag_engine.py
    ├── embedding_engine.py
    ├── dataset_agent.py
    ├── ocr_engine.py
    ├── ingestion.py
    ├── analytics_engine.py
    ├── query_engine.py
    ├── main.py
    │
    ├── data/
    ├── processed/
    ├── metadata/
    │
    ├── requirements.txt
    ├── README.md
---

## 🚧 Roadmap

  ✅ Phase 1
  	•	Core pipeline
  	•	Data cleaning & execution
  
  ✅ Phase 2
  	•	Multi-agent system
  	•	RAG integration
  	•	Intelligent reasoning
  	•	Self-learning memory
  
  🔄 Phase 3 (Next)
  	•	Report generation (Excel, TXT)
  	•	Structured output formatting
  
  🔄 Phase 4
  	•	OCR for Indian languages
  	•	Advanced document ingestion
  
  🔄 Phase 5
  	•	Enhanced NLP understanding
  	•	Context-aware query interpretation
  
  💡 Future Improvements
  	•	Web UI (Streamlit / React)
  	•	Database integration (Postgres, APIs)
  	•	Real-time dashboards
  	•	Alert systems

---

👤 Author - Vishnu Chevvakula

⭐ If you like this project
Give it a star ⭐ and feel free to contribute!
