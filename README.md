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

### Google Drive (working store)

Canonical folder: [`1GebY2TnV4gbWhDfJQu-CV2lRPCH1mr-a`](https://drive.google.com/drive/folders/1GebY2TnV4gbWhDfJQu-CV2lRPCH1mr-a) (also in `config.example.json`).

Keep in that folder:

| File | Role |
|------|------|
| `transactions.csv` | Full ledger (one file) |
| `statement_manifest.json` | Processed PDF ids / modified times |
| `summary.json` | Aggregated totals |
| statement PDFs | Source documents |

**Drive MCP cannot carry the CSV.** Google Drive MCP `create_file` only accepts inline `textContent` / `base64Content`. That path truncates around ~16KB and must never be used for the ledger. Do not size-probe, chunk, or IMPORTRANGE-assemble.

**Correct upload path:**

1. Write CSV / manifest / summary to **local disk**.
2. Upload **from that path**:
   - Drive web UI file picker (browser) pointed at the local file, or
   - `python -c "from statements.drive_io import upload_from_disk; print(upload_from_disk('transactions.csv'))"` when `GOOGLE_DRIVE_TOKEN` or Application Default Credentials are already present.
3. `drive_io.upload_from_disk` uses Drive API `MediaFileUpload` (resumable). If credentials are missing it fails closed — it does not invent tokens or fall back to MCP inline content.

### Phase 2: Incremental sync

Default flow after bootstrap: merge **new/changed** PDFs only.

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

# Optional: from-disk Drive replace after sync (needs GOOGLE_DRIVE_TOKEN or ADC)
python -m statements.sync \
  --csv transactions.csv \
  --manifest statement_manifest.json \
  --drive-index drive_index.json \
  --pdf-folder ./downloaded_pdfs \
  --summary summary.json \
  --upload-drive \
  --drive-csv-file-id <transactions.csv Drive file id>
```

**How it works:**
- `statement_manifest.json` tracks each Drive PDF by file ID and `modifiedTime`
- Changed or new PDFs are parsed; their statement period replaces any existing rows for that period
- Unchanged PDFs are skipped entirely (no re-parsing)
- Rebuild only if no local CSV exists (bootstrap from in-situ Drive PDFs)

### Next phases

- **Phase 3:** Optional Grok briefing from aggregated summaries only (minimal tokens)
