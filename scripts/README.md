# AVID Database Scripts

Scripts for managing the AVID vulnerability database workflow.

## Workflow Overview

### Step 1: Data Collection
Use `avidtools/scripts/mileva.py` to scrape CVE data and generate reports:

```bash
cd avidtools/scripts
python mileva.py --output-dir ../../avid-db/reports/review
```

This creates timestamped JSONL files like `cve_digest_20251206_143052.jsonl` in the review folder.

### Step 2: Review and Publishing
Use `avid-db/scripts/publish.py` to:
- Assign AVID Report IDs
- Optionally create Vulnerabilities from Reports
- Assign AVID Vulnerability IDs
- Publish to final locations

```bash
cd avid-db/scripts

# Preview what would be done (dry run)
python publish.py ../reports/review/cve_digest_20251206_143052.jsonl --dry-run

# Publish reports only
python publish.py ../reports/review/cve_digest_20251206_143052.jsonl

# Publish reports AND create vulnerabilities
python publish.py ../reports/review/cve_digest_20251206_143052.jsonl --create-vulns

# Specify year for IDs (default: current year)
python publish.py ../reports/review/cve_digest_20251206_143052.jsonl --year 2025
```

## Scripts

### `review/default.py`
General review script for draft report files (`.json` or `.jsonl`) before publishing.

This script:
- Applies OpenAI/GPT artifact normalization (`type: "System"`)
- Applies developer mapping from model name (`Llama`→`Meta`, `Mistral`→`Mistral`, `DeepSeek`→`DeepSeek`)
- Saves normalized updates back to the input file in place
- Does not assign AVID IDs

**Examples:**
```bash
# Review a JSONL digest file in place
python review/default.py ../reports/review/cve_digest_20260219_103343.jsonl

# Review a single JSON report in place
python review/default.py ../reports/review/draft_report.json

# Preview without modifying the file
python review/default.py ../reports/review/cve_digest_20260219_103343.jsonl --dry-run
```

### `review/inspect.py`
Inspect Evals-specific reviewer for report JSON files.

This script updates Inspect benchmark description content and then applies the
same shared normalizations used by `review/default.py`.

### `publish.py`
Main publishing script for processing reports from the review folder.

**Arguments:**
- `input_path`: Path to JSONL or JSON file containing reports
- `--create-vulns`: Create vulnerabilities from reports (default: False)
- `--year YYYY`: Year for ID generation (default: current year)
- `--dry-run`: Preview actions without making changes
- `--delete-source`: Delete input file after successful publish

**Examples:**
```bash
# Process JSONL file, just assign report IDs
python publish.py ../reports/review/cve_digest_20251206_143052.jsonl

# Process and create vulnerabilities
python publish.py ../reports/review/cve_digest_20251206_143052.jsonl --create-vulns

# Process single JSON file
python publish.py ../reports/review/draft_report.json --create-vulns

# Dry run to see what would happen
python publish.py ../reports/review/cve_digest_20251206_143052.jsonl --create-vulns --dry-run

# Publish and delete source review file when complete
python publish.py ../reports/review/cve_digest_20251206_143052.jsonl --delete-source
```

### `utils/id_manager.py`
Manages AVID ID generation and tracking.

**Functions:**
- `get_next_report_id(year)`: Generate next available Report ID
- `get_next_vuln_id(year)`: Generate next available Vulnerability ID
- `parse_avid_id(avid_id)`: Parse an AVID ID into components
- `validate_avid_id(avid_id)`: Validate AVID ID format

### `utils/publisher.py`
Core publishing functionality.

**Functions:**
- `load_report_from_json(file_path)`: Load Report from JSON
- `save_report_to_json(report, file_path)`: Save Report to JSON
- `save_vulnerability_to_json(vuln, file_path)`: Save Vulnerability to JSON
- `assign_report_id(report, report_id)`: Assign ID to Report
- `create_vulnerability_from_report(report, vuln_id)`: Convert Report to Vulnerability
- `publish_report(report, report_id, year)`: Publish Report to final location
- `publish_vulnerability(vuln, vuln_id, year)`: Publish Vulnerability to final location

## Directory Structure

```
avid-db/
├── reports/
│   ├── review/          # Incoming reports (no IDs assigned yet)
│   │   └── cve_digest_20251206_143052.jsonl
│   ├── 2024/            # Published reports for 2024
│   │   └── AVID-2024-R0001.json
│   └── 2025/            # Published reports for 2025
│       └── AVID-2025-R0001.json
├── vulnerabilities/
│   ├── 2024/            # Published vulnerabilities for 2024
│   │   └── AVID-2024-V001.json
│   └── 2025/            # Published vulnerabilities for 2025
│       └── AVID-2025-V001.json
└── scripts/
    ├── publish.py       # Main publishing script
    └── utils/
        ├── id_manager.py   # ID generation
        └── publisher.py    # Publishing utilities
```

## ID Format

- **Report IDs**: `AVID-YYYY-R####` (e.g., `AVID-2025-R0001`)
- **Vulnerability IDs**: `AVID-YYYY-V###` (e.g., `AVID-2025-V001`)

IDs are automatically generated sequentially based on existing files in the database.
