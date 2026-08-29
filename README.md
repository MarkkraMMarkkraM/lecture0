# baseline

Fresh start — this is the baseline repository for new projects.

## Statement parser (Phase 1)

Parses **Emirates NBD** credit card PDF statements into a structured CSV. Uses code only — no AI tokens.

### Setup

```bash
pip install -r requirements.txt
```

### Usage

Place PDF statements in a folder (or pass individual files), then run:

```bash
python -m statements.ingest ./data/statements -o transactions.csv --summary summary.json
```

**Output:**
- `transactions.csv` — every transaction with dates, merchant, amount (AED), category
- `summary.json` — totals and spend by category

### Categories (rule-based)

Groceries, dining, subscriptions, transport, fees, insurance, etc. Rules live in `statements/categorize.py` and can be extended without AI.

### Google Drive

Your statements folder ID is in `config.example.json`. From Cursor, I can pull PDFs from Drive, run the parser, and return the CSV/summary here.

### Next phases

- **Phase 2:** Auto-ingest new statements from Drive; month-over-month comparison
- **Phase 3:** Optional Grok briefing from aggregated summaries only (minimal tokens)
