# Claude Code Usage Analytics Platform

An end-to-end platform to process, analyze, and visualize telemetry data from Claude Code sessions.

## Project Structure
```text
.
├── data/               # Raw telemetry and employee data
├── db/                 # SQLite database and schema
├── scripts/            # Ingestion and data generation scripts
├── src/                # Core analytics logic
├── dashboard.py        # Streamlit entry point (root)
├── PRESENTATION.md     # Executive summary and LLM usage log
├── README.md           # Project documentation
└── requirements.txt    # Project dependencies
```

## Setup & Execution

### 1. Environment Setup
Install the necessary libraries:
```bash
pip install -r requirements.txt
```

### 2. Data Preparation
To generate a fresh synthetic dataset:
```bash
python3 scripts/generate_fake_data.py --num-users 50 --num-sessions 1000 --days 30 --output-dir data
```

### 3. Ingestion
Process the raw logs into the structured SQLite database:
```bash
python3 scripts/ingest_data.py
```

### 4. Visualization
Launch the interactive dashboard:
```bash
streamlit run dashboard.py
```

## Business Insights
Detailed findings on cost efficiency, tool performance, and engineering productivity can be found in **[PRESENTATION.md](PRESENTATION.md)**.

