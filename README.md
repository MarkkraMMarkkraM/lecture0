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

Your statements folder ID is in `config.example.json`. From Cursor, say **"process my statements"** and I will:

1. List PDFs in your Drive statements folder
2. Download only new or changed statements (tracked in `statement_manifest.json`)
3. Run incremental sync into `transactions.csv`
4. Upload updated CSV, manifest, and summary back to Drive

### Phase 2: Incremental sync

After the initial full parse, new statements are merged automatically:

```bash
# Build drive-index from manifest (or from a Drive file listing)
python -m statements.build_drive_index statement_manifest.json -o drive_index.json

# Sync: skip unchanged PDFs, parse and merge new/changed ones
python -m statements.sync \
  --csv transactions.csv \
  --manifest statement_manifest.json \
  --drive-index drive_index.json \
  --pdf-folder ./downloaded_pdfs \
  --summary summary.json
```

**How it works:**
- `statement_manifest.json` tracks each Drive PDF by file ID and `modifiedTime`
- Changed or new PDFs are parsed; their statement period replaces any existing rows for that period
- Unchanged PDFs are skipped entirely (no re-parsing)

### Next phases

- **Phase 3:** Optional Grok briefing from aggregated summaries only (minimal tokens)
