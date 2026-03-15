## DebugIQ – AI-Powered Simulation Log Intelligence

DebugIQ is an AI-assisted debugging prototype for **semiconductor verification simulation logs**.  
It ingests large `.log` files, extracts structured failures, clusters similar issues, assigns **debug priority scores**, and provides **root-cause hints** plus an **interactive dashboard**.

---

## Features (High Level)

- **Log ingestion** from `logs/` with **synthetic log generation** if empty.
- **Regex parsing** of timestamp, severity, module, and message into a pandas DataFrame.
- **Log preprocessing** and **failure signatures** to detect duplicates / known bugs.
- **NLP classification** (TF‑IDF + Logistic Regression) into failure categories.
- **Semantic clustering** using sentence-transformers + KMeans.
- **Duplicate & frequency analysis**, **module hotspots**, and **regression health score**.
- **Priority scoring system** that ranks failures for debugging.
- **Known bug detection** via signature matching.
- **Root cause suggestions & debug recommendations** by rule-based heuristics.
- **SQLite storage** of all structured failures.
- **Streamlit + Plotly dashboard** for interactive exploration.
- **Text / Markdown debug reports** for sharing.

---

## Project Structure

```text
debugiq/
├── logs/                  # Raw simulation logs (auto-filled with synthetic logs if empty)
├── data/                  # SQLite DB + generated reports
├── parser.py              # Ingestion + regex parsing
├── preprocess.py          # Message cleaning + failure signatures
├── classifier.py          # TF-IDF + Logistic Regression categorizer
├── clustering.py          # Sentence-transformers embeddings + KMeans clustering
├── ranking.py             # Priority scoring, frequency, cluster size, module criticality
├── analysis.py            # Frequency, hotspots, regression health, summary
├── database.py            # SQLite schema + read/write
├── recommendations.py     # Root-cause suggestions + debug actions
├── report_generator.py    # Text + Markdown report generation
├── dashboard.py           # Streamlit + Plotly interactive dashboard
├── main.py                # Orchestration pipeline entrypoint
└── requirements.txt
```

---

## Setup

From the project root:

```bash
python -m venv venv
source venv/bin/activate          # macOS / Linux
# or: venv\Scripts\activate       # Windows

pip install --upgrade pip
pip install -r requirements.txt
```

> If you prefer manual installs, ensure at least:
> `pandas`, `scikit-learn`, `sentence-transformers`, `streamlit`, `plotly`, `regex`, `torch`.

---

## End-to-End Workflow

### 1. Run the Analysis Pipeline

```bash
python main.py
```

**What happens:**

1. **Log ingestion & synthetic generation** (`parser.ingest_and_parse`)
   - Reads all `.log` files under `logs/`.
   - If `logs/` is empty, `parser.generate_synthetic_logs` auto-creates realistic simulation logs with `INFO`, `WARNING`, `ERROR`, `FATAL` messages across modules like `CACHE_CTRL`, `MEMORY_CTRL`, `ALU`, `AXI_INTERFACE`.

2. **Regex parsing into DataFrame** (`parser.parse_logs_to_df`)
   - Extracts:
     - `timestamp`
     - `severity`
     - `module`
     - `message`
   - Produces a structured pandas DataFrame with `timestamp_parsed` as a helper time column.

3. **Preprocessing & failure signatures** (`preprocess.preprocess_logs`)
   - Normalizes `message`:
     - lowercasing
     - removing numbers
     - removing noise words
     - basic token cleanup
   - Stores result as `normalized_message`.
   - Generates deterministic `failure_signature` per normalized message (hash-based) to identify duplicates and known bugs.

4. **NLP-based failure categorization** (`classifier.categorize_failures`)
   - Uses TF‑IDF + Logistic Regression trained on a small heuristic dataset.
   - Classifies failures into:
     - `assertion failure`
     - `timeout error`
     - `protocol violation`
     - `data mismatch`
     - `memory error`
     - `unknown`
   - Output stored in `category`.

5. **Semantic failure clustering** (`clustering.add_clusters`)
   - Encodes `normalized_message` using a **sentence-transformers** model (default `all-MiniLM-L6-v2`).
   - Clusters the embedding vectors using **KMeans**.
   - Adds `cluster_id` to each failure so similar issues share a cluster.

6. **Priority scoring & frequency** (`ranking.compute_priority_scores`)
   - Computes:
     - `frequency`: number of occurrences per `failure_signature` (duplicate detection).
     - `cluster_size`: number of items per `cluster_id`.
     - `severity_score`: maps severity (`INFO`/`WARNING`/`ERROR`/`FATAL`) to numeric value.
     - `module_criticality`: configurable importance per module.
   - Calculates a **debug priority score**:
     \[
     \text{priority} = 0.4\cdot \text{severity\_score} +
                       0.3\cdot \log(\text{frequency}+1) +
                       0.2\cdot \text{cluster\_size} +
                       0.1\cdot \text{module\_criticality}
     \]
   - Sorts rows by `priority_score` (highest first) so you know what to debug first.

7. **Known bug detection** (`main.apply_known_bug_flags`)
   - Maintains a set `KNOWN_BUG_SIGNATURES` (signatures of known issues).
   - Sets `known_bug_flag` = 1 if a failure’s `failure_signature` is in that set.
   - Currently provided as a hook for you to populate with real signatures.

8. **Root-cause and debug recommendations** (`recommendations.add_recommendations`)
   - Adds:
     - `root_cause_suggestion`: rule-based explanation (e.g., timeout, protocol violation, data mismatch).
     - `debug_actions`: recommended steps (inspect handshakes, verify assertions, check memory transactions, etc.).

9. **Database storage (SQLite)** (`database.write_failures`)
   - Writes all enriched failures into `data/debugiq.db` table `failures` with fields:
     - `id` (auto)
     - `timestamp`
     - `module`
     - `severity`
     - `category`
     - `message`
     - `cluster_id`
     - `failure_signature`
     - `frequency`
     - `priority_score`
     - `known_bug_flag`

10. **Regression health score & summary** (`analysis.summarize_for_report`)
    - Computes:
      - total failures
      - unique failures
      - most frequent bug
      - highest priority bug
      - module hotspots
      - severity distribution
      - **regression health score** (0–100) based on counts, severity mix, and cluster diversity.

11. **Report generation** (`report_generator.save_report`)
    - Produces:
      - `data/debug_report.txt`
      - `data/debug_report.md`
    - Reports contain:
      - total + unique failures
      - most frequent bug
      - highest priority bug
      - problematic modules
      - regression health score

At the end of `python main.py` you should see a short console summary and be able to inspect the DB and reports under `data/`.

---

## Interactive Dashboard

After running `python main.py`, start the dashboard:

```bash
streamlit run dashboard.py
```

**What the dashboard shows (from SQLite data):**

1. **Regression health score card**
   - Top-level health metric (0–100).

2. **Failure category distribution**
   - Pie chart of categories (assertion / timeout / protocol / data mismatch / memory / unknown).

3. **Module hotspot bar chart**
   - Failures per module to highlight problematic blocks like `CACHE_CTRL`, `MEMORY_CTRL`, `AXI_INTERFACE`.

4. **Top priority failures table**
   - Sorted by `priority_score` with severity, module, category, frequency, cluster, and known bug flag.

5. **Failure timeline chart**
   - Scatter plot over `timestamp_parsed` vs. `priority_score` with color by severity.

6. **Cluster visualization**
   - Scatter of clusters (cluster size vs. average priority) to see dominant failure families.

7. **Known bugs list**
   - Table of failures where `known_bug_flag == 1` if you populate known signatures.

This dashboard provides a **debugging cockpit**: you can quickly see regression health, hotspots, and the most impactful failures to work on.

---

## Customizing for Your Environment

- **Plug in real logs**: Drop your real simulator logs into `logs/` with a similar line format to the synthetic examples.  
- **Tune module criticality**: Edit `MODULE_CRITICALITY` in `ranking.py` to reflect your design’s critical paths.  
- **Register known bugs**: Populate `KNOWN_BUG_SIGNATURES` in `main.py` with signatures of bugs you’ve already root-caused.  
- **Extend NLP / LLM**: Replace or augment `recommendations.suggest_root_cause` with an LLM call using your OpenAI-compatible endpoint if desired.

This setup is intended as a **hackathon-friendly, locally runnable prototype** that still follows a clean, modular, production-style architecture.

