# Review/Normalize Scripts

This folder contains CLI entrypoints for normalizing review files in place before publish.

## Scripts

- `default.py`
  - Generic normalize pass for `.json` and `.jsonl` files.
  - Uses `avidtools.connectors.base.normalize_file`.

- `inspect.py`
  - Inspect-specific normalize logic for single report JSON files.
  - Uses `avidtools.connectors.inspect.process_report`.
  - If an inspect benchmark cannot be resolved to supported categories,
    the report file is deleted.

- `garak.py`
  - Garak-specific normalize logic for `.json` and `.jsonl` files.
  - Uses `avidtools.connectors.garak.normalize_file`.

## Typical usage

```bash
python scripts/review/default.py reports/review/<file>.jsonl
python scripts/review/inspect.py reports/2025/AVID-2025-R0003.json
python scripts/review/garak.py reports/review/garak.<id>.avid.jsonl
```

Add `--dry-run` to `default.py` and `garak.py` to preview counts without writing files.
