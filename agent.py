# --- EXECUTION STRATEGY ENGINE ---
def get_execution_strategy(intent: str) -> str:
    """
    Map intent to analysis strategy.
    """
    strategies = {
        "comparison": "Compare groups using aggregation (groupby, mean, sum) and highlight differences",
        "trend": "Analyze changes over time (time-series grouping, growth rates)",
        "diagnostic": "Identify causes and drivers (segmentation, correlation, breakdown)",
        "predictive": "Estimate future values (trend extrapolation or patterns)",
        "anomaly": "Detect unusual values (outliers, deviations)",
        "analysis": "General aggregation and summarization"
    }
    return strategies.get(intent, "General analysis")
# --- Query Intent Detection Engine ---
def detect_query_intent(query: str) -> str:
    """
    Detect high-level business intent.
    """
    q = query.lower()

    if any(k in q for k in ["compare", "vs", "versus"]):
        return "comparison"

    if any(k in q for k in ["trend", "over time", "growth", "decline"]):
        return "trend"

    if any(k in q for k in ["why", "reason", "cause"]):
        return "diagnostic"

    if any(k in q for k in ["predict", "forecast"]):
        return "predictive"

    if any(k in q for k in ["anomaly", "outlier", "unusual"]):
        return "anomaly"

    return "analysis"
# TODO: Replace ask_llm with pluggable LLM interface (OpenAI / Ollama / local models)
from llm_engine import ask_llm
llm_cache = {}

# --- Persistent LLM cache ---
import json
CACHE_FILE = "llm_cache.json"

# --- SELF-LEARNING MEMORY SYSTEM ---
MEMORY_FILE = "agent_memory.json"
agent_memory = {}

def load_memory():
    global agent_memory
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                agent_memory = json.load(f)
        except:
            agent_memory = {}

def save_memory():
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(agent_memory, f)
    except:
        pass

MAX_CACHE_SIZE = 500  # limit entries

# Load cache from disk if exists
def load_cache():
    global llm_cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                llm_cache = json.load(f)
        except:
            llm_cache = {}

# Save cache to disk
def save_cache():
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(llm_cache, f)
    except:
        pass

def cached_llm(prompt, cache_type="general"):
    """
    Advanced cache:
    - exact match
    - semantic (substring similarity)
    - type-aware caching
    - eviction
    """

    key = f"{cache_type}:{prompt}"

    # Exact match
    if key in llm_cache:
        return llm_cache[key]

    # Semantic cache (simple heuristic)
    for existing_key in llm_cache:
        if cache_type in existing_key:
            existing_prompt = existing_key.split(":", 1)[-1]
            if prompt in existing_prompt or existing_prompt in prompt:
                return llm_cache[existing_key]

    # Call LLM
    response = ask_llm(prompt, "")

    # Eviction (if cache too large)
    if len(llm_cache) > MAX_CACHE_SIZE:
        # remove oldest entry
        first_key = list(llm_cache.keys())[0]
        llm_cache.pop(first_key)

    llm_cache[key] = response
    save_cache()
    return response
from dataset_agent import load_catalog
from ingestion import load_file
import os
from rag_engine import retrieve
from rag_engine import embedding_engine

# --- Embedding model selection helper ---
def select_embedding_model_for_query(query: str) -> str:
    q = query.lower().strip()

    if len(q.split()) > 8 or any(k in q for k in ["analyze", "analysis", "why", "compare", "trend", "insight"]):
        return "accurate"

    if len(q.split()) <= 4:
        return "fast"

    return "mini"
from document_loader import load_documents
from rag_engine import add_document

# --- Heuristic column similarity helpers ---
def normalize_col(col):
    return col.lower().replace("_", "").replace(" ", "")

def col_similarity(c1, c2):
    """
    Simple similarity:
    - exact match after normalization
    - substring overlap
    - token overlap
    """
    n1 = normalize_col(c1)
    n2 = normalize_col(c2)

    if n1 == n2:
        return 1.0

    # substring match
    if n1 in n2 or n2 in n1:
        return 0.8

    # token overlap
    tokens1 = set(c1.lower().replace("_", " ").split())
    tokens2 = set(c2.lower().replace("_", " ").split())
    overlap = len(tokens1 & tokens2)
    total = max(len(tokens1), len(tokens2), 1)
    return overlap / total

# Load cache at startup
load_cache()
load_memory()


def generate_plan(query, df_columns, strategy):
    prompt = f"""
You are an AI planner.

User query: {query}
Strategy: {strategy}
Available columns: {df_columns}

IMPORTANT:
- There may be MULTIPLE datasets merged together
- Identify relationships across columns (e.g., branch, date, product, employee)
- If document context is available, incorporate it into planning
- Use document insights to guide what data to analyze

Break the task into clear steps.

Rules:
- Max 5 steps
- Include:
    1. What data to use
    2. If JOIN/merge logic is needed
    3. What transformation (groupby, compare, correlation, etc.)
    4. What business insight is expected

Return ONLY numbered steps.
"""
    return cached_llm(prompt, "plan").strip()

# Step 1: Reasoning function
def generate_reasoning(query, df_columns, df_dtypes, plan):
    prompt = f"""
You are a senior BUSINESS DATA ANALYST (like McKinsey/Bain/BCG).

DataFrame columns: {df_columns}
Data types: {df_dtypes}

User query: {query}

(Query may include document context)

Plan:
{plan}

Think like a business analyst, NOT a statistician.

GOALS:
- Identify key business metrics (revenue, sales, quantity, price, geography, product, time)
- Focus on insights, not just statistics
- Avoid meaningless describe() unless absolutely necessary
- Detect relationships across datasets (e.g., cost vs performance, employee vs sales)
- Compare metrics across groups
- Identify patterns (high vs low performers)

STEP 1: Understand business intent behind the query
STEP 2: Identify IMPORTANT columns (sales, product, geography, time, etc.)
STEP 3: Decide BEST analysis:
    - Trends (time-based)
    - Segmentation (product, region, customer)
    - Performance (top/bottom performers)
    - Aggregation (sum, growth, contribution)
STEP 4: Define clear approach (groupby, aggregation, comparison)

IMPORTANT RULES:
- PRIORITIZE columns like SALES, PRODUCTLINE, COUNTRY, DEALSIZE, YEAR, etc.
- IGNORE irrelevant IDs unless necessary
- DO NOT default to describe()
- Focus on actionable insights

Return ONLY a SHORT plan (max 4 lines).
"""
    reasoning = cached_llm(prompt, "reasoning").strip()
    return reasoning

# Step 2: Update code generation function to accept reasoning
def generate_code(query, df_columns, df_dtypes, reasoning):
    """
    Ask LLM to generate pandas code
    """
    prompt = f"""
You are a STRICT data analysis engine.

You are NOT allowed to behave like ChatGPT.
You MUST follow rules exactly.

DataFrame columns: {df_columns}
Data types: {df_dtypes}

User query: {query}

Analysis plan:
{reasoning}

IMPORTANT:
- Data may come from MULTIPLE merged datasets
- You may need to compare columns from different sources
- Prefer groupby + comparison logic
- If document context suggests relationships, reflect that in analysis logic

CRITICAL RULES (NO EXCEPTIONS):
- You MUST use ONLY the provided DataFrame `df`
- You MUST NOT create any new DataFrame
- You MUST NOT hardcode or simulate data
- You MUST NOT use pd.DataFrame()
- You MUST NOT use read_csv or any file operations
- You MUST NOT use print()
- You MUST NOT import anything
- You MUST NOT redefine df
- You MUST NOT include ANY text before or after code
- If you do NOT follow rules, your answer is WRONG
- If task is not possible → result = "Not possible with given data"

OUTPUT FORMAT (STRICT):
result = <pandas expression>

No explanations. No text. ONLY code.
"""
    code = cached_llm(prompt, "code").strip()
    # Clean markdown / text artifacts
    if "```" in code:
        code = code.replace("```python", "").replace("```", "").strip()
    return code


def store_failure_case(query, reasoning, code, error):
    key = query[:100]  # truncate key
    agent_memory[key] = {
        "reasoning": reasoning,
        "code": code,
        "error": str(error)
    }
    save_memory()

def execute_code(code, df, retries=2):
    local_vars = {"df": df}

    try:
        print("\n[Generated Code]:\n", code)
        # Ensure result assignment exists
        if "result =" not in code:
            code = "result = " + code.strip()
        # Basic guardrails
        forbidden = [
            "import",
            "read_csv",
            "DataFrame(",
            "print(",
            "plt",
            "matplotlib",
            "open(",
            "__",
            "eval(",
            "exec(",
            "=" + " pd.",  # catches reassignment patterns
            "Here is",
            "example"
        ]
        if any(f in code for f in forbidden):
            return "Unsafe code detected"

        exec(code, {}, local_vars)
        return local_vars.get("result", "No result returned")

    except Exception as e:
        if retries > 0:
            fix_prompt = f"""
The following Python code has an error:

{code}

Error:
{e}

Fix the code. Return ONLY corrected Python code.
"""

            fixed_code = cached_llm(fix_prompt, "fix").strip()
            # Clean markdown / text artifacts
            if "```" in fixed_code:
                fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
            return execute_code(fixed_code, df, retries-1)

        store_failure_case("unknown_query", code, code, e)
        return f"Execution failed after retries: {e}"

def score_datasets_by_query(query: str, catalog: dict):
    """
    Score datasets using semantic_tags, important_columns, and use_cases.
    Returns list of (file, score) sorted desc.
    """
    q = query.lower()
    scores = []

    for file, meta in catalog.items():
        score = 0

        # semantic tags
        for tag in meta.get("semantic_tags", []):
            if tag.lower() in q:
                score += 3

        # important columns
        for col in meta.get("important_columns", []):
            if col.lower() in q:
                score += 2

        # use cases
        for uc in meta.get("use_cases", []):
            if any(word in uc.lower() for word in q.split()):
                score += 1

        scores.append((file, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores

def select_datasets_llm(query):
    """
    Use LLM + catalog knowledge to select one or more relevant datasets.
    Returns list of filenames.
    """
    catalog = load_catalog()

    if not catalog:
        return []

    # --- Heuristic selection using catalog ---
    scored = score_datasets_by_query(query, catalog)

    # If strong signal, pick top datasets
    top = [f for f, s in scored if s > 0][:3]

    if top:
        print("[Heuristic Dataset Selection]:", top)
        return top

    prompt = f"""
You are an AI data system.

Available datasets (with descriptions and use cases):
{catalog}

User query: {query}

Additional document context (if any):
{retrieve(query)}

Decide which dataset(s) are required to answer the query.

Return ONLY a Python list of dataset file names.
Example: ["sales.csv"] or ["sales.csv", "employees.csv"]
"""

    response = cached_llm(prompt, "dataset_selection").strip()

    # clean markdown if any
    if "```" in response:
        response = response.replace("```python", "").replace("```", "").strip()

    try:
        files = eval(response)
        if isinstance(files, list):
            return list(set(files))
    except:
        pass

    # fallback: return first dataset
    return list(catalog.keys())[:1]

def merge_datasets(dfs, query):
    """
    Intelligent merge using LLM to decide join keys.
    """
    if not dfs:
        return None

    df = dfs[0]

    for other in dfs[1:]:
        cols1 = df.columns.tolist()
        cols2 = other.columns.tolist()

        # --- Semantic join hints from catalog ---
        catalog = load_catalog()
        potential_keys = set()

        for file, meta in catalog.items():
            for key in meta.get("potential_joins", []):
                potential_keys.add(key.lower())

        # --- Heuristic join detection ---
        best_match = None
        best_score = 0

        for c1 in cols1:
            for c2 in cols2:
                score = col_similarity(c1, c2)

                # Boost score if matches semantic join keys
                if c1.lower() in potential_keys or c2.lower() in potential_keys:
                    score += 0.3
                if score > best_score:
                    best_score = score
                    best_match = (c1, c2)

        # Threshold for confident match
        if best_match and best_score >= 0.75:
            c1, c2 = best_match
            try:
                df = df.merge(other, left_on=c1, right_on=c2)
                print(f"[Semantic-Heuristic Merge]: {c1} ↔ {c2} (score={round(best_score,2)})")
                continue
            except Exception as e:
                print(f"Heuristic merge failed: {e}")

        # --- LLM fallback if heuristic fails ---
        prompt = f"""
You are a senior data engineer.

Dataset 1 columns: {cols1}
Dataset 2 columns: {cols2}

User query: {query}

IMPORTANT:
- Try to find SEMANTIC relationships, not just exact matches
- Examples:
    branch ~ branch_name ~ location
    date ~ order_date ~ transaction_date
    employee_id ~ staff_id

Rules:
- Prefer exact matches
- Otherwise find closest semantic match
- If multiple possible joins → choose BEST one
- If no meaningful relationship → return NONE

Return ONLY:
- column name
OR
- NONE
"""

        join_col = cached_llm(prompt, "join").strip()

        # clean response
        if "```" in join_col:
            join_col = join_col.replace("```", "").strip()

        join_col = join_col.replace('"', '').replace("'", "").strip()

        if join_col != "NONE" and join_col in cols1 and join_col in cols2:
            try:
                df = df.merge(other, on=join_col)
                print(f"[Merged on]: {join_col}")
            except Exception as e:
                print(f"Merge failed on {join_col}: {e}")
        else:
            print("[No valid join found, skipping dataset]")

    return df


def generate_insights(query, result):
    prompt = f"""
You are a senior business analyst.

User query:
{query}

Computed result:
{result}

TASK:
Extract HIGH-QUALITY BUSINESS INSIGHTS.

RULES:
- Focus on BUSINESS meaning (sales, demand, growth, performance)
- Translate technical/statistical info into business impact
- IGNORE methodology unless it affects decisions
- Evaluate if change is meaningful (real vs noise)
- Identify growth, decline, or stagnation
- NO technical jargon unless necessary
- Be decisive and practical
Return 3-5 bullet insights.
"""
    return cached_llm(prompt, "insights").strip()

# --- WHY/causal reasoning layer ---
def generate_why_analysis(query, result, rag_text):
    prompt = f"""
You are a senior business consultant.

User query:
{query}

Computed result:
{result}

Document context (if any):
{rag_text}

TASK:
Identify REAL DRIVERS behind the outcome.


RULES:
- Focus on REAL BUSINESS DRIVERS (demand, pricing, seasonality, segments)
- IGNORE statistical methodology unless it impacts business meaning
- Translate document info into business reasoning
- Avoid academic/statistical explanations
- No vague or generic statements

Return 3-5 bullet points.
"""
    return cached_llm(prompt, "why").strip()

# --- DECISION layer ---
def generate_decision(query, result, insights, why_analysis):
    prompt = f"""
You are a senior business decision-maker.

User query:
{query}

Insights:
{insights}

Why analysis:
{why_analysis}

TASK:
Provide clear BUSINESS ACTIONS.

RULES:
- Be practical and specific
- Include 3-5 actions
- Prioritize what to DO next
- Include risk/caution if needed
- No generic advice

Return ONLY bullet points.
"""
    return cached_llm(prompt, "decision").strip()

def select_context(query, df):
    columns = df.columns.tolist()

    prompt = f"""
You are a data analyst.

Columns: {columns}
Query: {query}

Select ONLY relevant columns needed.
Return as Python list.
"""

    selected = cached_llm(prompt, "context").strip()

    try:
        selected_cols = eval(selected)
        return df[selected_cols]
    except:
        return df

def run_agent(query, df=None):

    # --- Select embedding model dynamically ---
    try:
        model_key = select_embedding_model_for_query(query)
        embedding_engine.switch_model(model_key)
        print(f"[Embedding Model Selected]: {model_key}")
        print("[Embedding Info]:", embedding_engine.info())
    except Exception as e:
        print(f"[Embedding Model Selection Error]: {e}")

    # --- Detect query intent ---
    intent = detect_query_intent(query)
    print(f"[Detected Intent]: {intent}")

    # --- Decide query type (structured vs unstructured vs hybrid) ---
    routing_prompt = f"""
Classify the query:

Query: {query}

Return ONLY one word:
- "structured"
- "unstructured"
- "hybrid" (if both data + documents needed)
"""

    route = cached_llm(routing_prompt, "routing").strip().lower()

    # Always try RAG (do NOT depend only on routing)
    rag_context = retrieve(query)

    rag_text = ""
    if rag_context:
        rag_text = "\n".join(rag_context[:5])  # limit context

    if rag_text:
        print("\n[RAG Context Used]:")
        print(rag_text[:500])

    # Step 1: select dataset
    selected_files = select_datasets_llm(query)

    # Fallback: if LLM fails to select datasets, use all available datasets
    if not selected_files:
        catalog = load_catalog()
        selected_files = list(catalog.keys())
        print("[Fallback Triggered]: Using all datasets")

    print("\n[Selected Datasets]:", selected_files)

    dfs = []
    for file in selected_files:
        file_path = os.path.join("data", file)
        try:
            dfs.append(load_file(file_path))
        except Exception as e:
            print(f"Failed to load {file}: {e}")

    if not dfs:
        # Force RAG usage if any context exists
        if rag_context:
            rag_text = "\n".join(rag_context[:5])

            rag_answer_prompt = f"""
You are a STRICT document analyst.

User query:
{query}

Relevant document excerpts:
{rag_text}

RULES:
- Answer ONLY using the provided excerpts
- MUST cite sources like [Source: filename, Page X]
- DO NOT be generic
- If insufficient info, say "Insufficient information"

TASK:
- Extract ONLY business-relevant meaning
- Ignore statistical/technical noise
- Explain what this means for sales, demand, or performance
- Be concise and practical
"""
            rag_answer = cached_llm(rag_answer_prompt, "rag_answer")

            return {
                "generated_code": None,
                "result": rag_text,
                "explanation": rag_answer
            }

        return "No dataset available and no relevant documents found"

    df = merge_datasets(dfs, query)
    if df is not None and df.shape[1] > 50:
        print("[Warning]: Large merged dataset - possible incorrect join")
    df = df.copy()

    if df is None:
        return "No dataset available"

    # --- Inject RAG context into reasoning ---
    if rag_text:
        query = f"""
User Query:
{query}

Additional Context from documents:
{rag_text}
"""

    df = select_context(query, df)
    print("\n[Selected Columns]:", df.columns.tolist())

    # --- Step: planning ---
    strategy = get_execution_strategy(intent)
    print(f"[Execution Strategy]: {strategy}")
    plan = generate_plan(query, list(df.columns), strategy)
    print("\n[Plan]:\n", plan)

    # Step 2: generate reasoning step
    df_dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
    reasoning = generate_reasoning(
        f"{query}\n\nDetected Intent: {intent}\n\nPast Mistakes: {agent_memory}",
        list(df.columns),
        df_dtypes,
        plan
    )
    print("\n[Reasoning Steps]:\n", reasoning)

    # Step 3: generate code using reasoning
    code = generate_code(
        f"{query}\n\nIntent: {intent}\n\nExecution Plan:\n{plan}",
        list(df.columns),
        df_dtypes,
        reasoning
    )

    # Validation step
    validation_prompt = f"""
You are a strict code validator.

Check if the following code strictly follows rules:
- Uses ONLY df
- No imports
- No new DataFrame creation
- No print statements
- Assigns result variable

Code:
{code}

Return ONLY:
- "valid"
- "invalid"
"""

    validation = cached_llm(validation_prompt, "validation").strip().lower()

    if "invalid" in validation:
        return {
            "error": "Generated code failed validation",
            "generated_code": code
        }

    # Step 4: execute code
    result = execute_code(code, df)
    print("\n[Execution Result]:\n", result)

    # Step 5: self-evaluation loop
    evaluation_prompt = f"""
User query: {query}
Reasoning: {reasoning}
Result: {result}

Evaluate if result correctly answers the query.

Return ONLY:
- "good" if correct
- "bad" if incorrect
Also check:
- Does it enable meaningful business insight?
- Not just raw aggregation
"""
    evaluation = cached_llm(evaluation_prompt, "evaluation").strip().lower()

    if "bad" in evaluation:
        store_failure_case(query, reasoning, code, "bad result")
        print("\n[Self Correction Triggered]")
        reasoning = generate_reasoning(
            f"{query}\n\nDetected Intent: {intent}\n\nPast Mistakes: {agent_memory}",
            list(df.columns),
            df_dtypes,
            plan
        )
        code = generate_code(
            f"{query}\n\nIntent: {intent}\n\nExecution Plan:\n{plan}",
            list(df.columns),
            df_dtypes,
            reasoning
        )
        result = execute_code(code, df)

    # Step 6: explanation (context-aware)
    explanation_prompt = f"""
You are a STRICT business analyst.

User query:
{query}

Computed result:
{result}

Document context (if any):
{rag_text}

RULES:
- Base explanation PRIMARILY on computed result
- Use document context ONLY if it directly supports the result
- If using document context → MUST cite [Source: ...]
- DO NOT say "based on documents"
- DO NOT hallucinate
- If result is insufficient → clearly say so
- Translate technical/statistical findings into BUSINESS implications
- Avoid academic/statistical language unless necessary
- Focus on sales, demand, growth and decision impact

TASK:
Give a concise explanation that:
- Connects computed results with document insights (if relevant)
- Highlights WHY patterns exist (not just WHAT)
"""

    insights = generate_insights(query, result)
    print("\n[Insights]:\n", insights)

    why_analysis = generate_why_analysis(query, result, rag_text)
    print("\n[Why Analysis]:\n", why_analysis)

    decision = generate_decision(query, result, insights, why_analysis)
    print("\n[Decision]:\n", decision)

    explanation_text = cached_llm(explanation_prompt, "explanation")

    explanation = f"""
Insights:
{insights}

Why:
{why_analysis}

Decision:
{decision}

Explanation:
{explanation_text}
"""

    # Save snapshot for debugging / audit
    try:
        os.makedirs("processed", exist_ok=True)
        df.to_csv("processed/last_used_data.csv", index=False)
    except Exception as e:
        print(f"Snapshot save failed: {e}")

    return {
        "generated_code": code,
        "result": result,
        "explanation": explanation
    }