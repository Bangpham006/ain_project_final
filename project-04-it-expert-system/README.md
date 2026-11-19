# Project 04 — IT Troubleshooting Expert System

Offline rule-based diagnostic expert system for the FIT HANU campus IT helpdesk across five support domains (`hanu_wifi`, `fit_lms`, `lab_computers`, `hanu_account`, and `fit_printer`), built from first principles in Python 3.11 without external rule-engine libraries or hosted LLM APIs.

- **GitHub Repository:** `https://github.com/Bangpham006/ain_project_final`
- **Python Version:** **Python 3.11** (`3.11.x`)

---

## 1. Prerequisites & Installation

From inside this `code/` directory (or `project-04-it-expert-system/`), create a Python 3.11 virtual environment and install pinned dependencies:

```bash
# macOS / Linux
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```powershell
# Windows (PowerShell)
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 2. Run the Interactive Application (Single Command)

```bash
streamlit run starter/app.py
```

*(On Windows PowerShell without activating `.venv`: `.venv\Scripts\python.exe -m streamlit run starter/app.py`)*

### Key Product Capabilities
- **5-Domain Symptom Checklists & Search:** Categorised tabs with active counters and instant keyword/ID filtering.
- **Scenario & Multi-Fault Presets:** One-click sidebar fixtures (`SC01`–`SC15`) plus multi-domain concurrent stress presets (`STRESS_MF01`, `STRESS_MF02`).
- **Offline Layered SVG Visual Reasoning Graph:** Pure-Python responsive proof & conflict DAG (`starter/reasoning_graph.py`) plus Graphviz DOT export.
- **Dynamic Follow-Up Questioning:** Ranked what-if consultation (`suggest_followups`) with `Yes` / `No` session memory across both ambiguous (`SC04`) and empty (`SC06`) states, isolating contradictory prompts (`X01`–`X05`).
- **Live Rule-Ablation Sandbox:** Disable any subset of rules (e.g., `R007` on `SC04`) directly in the sidebar to observe `ambiguous` transition to `resolved`.

---

## 3. Reproduce Report Tables, Figures & Automated Tests

Reproduce every CSV table, markdown audit, and PNG figure used in the Final Report (`experiments/results/`):

```bash
python scripts/run_experiments.py
```

Execute the complete 86-test automated verification suite (schema sanity, deductive core, monotonicity/invariance, CLI, and headless Streamlit UI):

```bash
pytest tests/ -v
```

Optional terminal consultation demo (Midterm CLI):

```bash
python starter/demo_cli.py --scenario SC04 --ask
```

---

## 4. Directory Structure

```text
code/
├── README.md                       # Setup, single-command run, and reproducibility guide
├── requirements.txt                # Pinned Python 3.11 dependencies
├── data/
│   ├── symptoms.json               # 27 campus IT symptoms across 5 domains
│   ├── causes.json                 # 14 diagnostic causes & remediation actions
│   ├── rules.json                  # 48 definite Horn production rules
│   ├── scenarios.json              # 15 benchmark scenarios (SC01-SC15)
│   ├── conflicts.json              # 5 meta-level printer conflict constraints (X01-X05)
│   └── README.md                   # Data dictionary & schema notes
├── starter/
│   ├── student_core.py             # Pure-Python forward-chaining core, explain, clustering & follow-ups
│   ├── reasoning_graph.py          # Pure-Python offline SVG & Graphviz DOT reasoning graph builder
│   ├── app.py                      # Interactive Streamlit diagnostic workstation
│   ├── conflicts.py                # Schema validator & loader for conflicts.json
│   ├── rule_loader.py              # Starter KB schema loader
│   └── demo_cli.py                 # Interactive command-line consultation interface
├── scripts/
│   └── run_experiments.py          # Single-command reproducibility runner for all report tables/figures
├── experiments/
│   ├── ablation.py                 # Experiments E0-E9 (ablation, strategies, baselines, formal bounds)
│   ├── reasoning_probes.py         # Automated evidence generator for SC01-SC15 oral-defence probes
│   ├── product_eval.py             # Final milestone comparison (Table 3), scenario matrix (Table 6) & figures
│   ├── data_issues.md              # Documented KB anomalies (CAUSE13/14 swap, R048, tag drift)
│   └── results/                    # Generated CSVs, markdown reports, and 300-DPI PNG figures
└── tests/
    ├── test_project_04_sanity.py   # Starter schema & entry-point sanity tests
    ├── test_project_04_core.py     # 71 exhaustive deductive, ablation, and CLI tests
    └── test_project_04_app.py      # Headless Streamlit AppTest & SVG reasoning-graph tests
```
