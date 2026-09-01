# CLI — Layer 3

> Parent: [../main_markdown.md](../main_markdown.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Command-line interface for running spectral analysis locally without the Flask server. Useful for testing, debugging, and batch processing.

## Tech stack & conventions
- Python argparse for CLI argument parsing
- Calls same `process_input()` as the server
- stdout output with formatted results

## Structure
```
cli/
├── main.py                # CLI entry point (244 lines)
└── step2_test_router.py   # Near-duplicate integration test
```

## Entry points
- `python main.py --json FILE.json [options]`
- `python main.py --frame 'JSON_INLINE' [options]`

## Key interactions
- **Input:** `--json` (file path) or `--frame` (inline JSON)
- **Options:** `--picos`, `--cumplimiento`, `--lic`, `--corr`, `--dane`/`--danes`, `--umbral_db`, `--delta_fc_khz`, `--delta_bw_khz`
- **Processing:** Calls `src.processor.process_input()` — same pipeline as server
- **Output:** Formatted JSON to stdout via `print_full_response()`

## Common tasks & gotchas
- `step2_test_router.py` is a near-duplicate of `main.py` with minor differences (missing `--delta_fc_khz`/`--delta_bw_khz`)
- `parse_picos_arg` and `parse_danes_arg` are copy-pasted here too — 3rd copy
- If `--cumplimiento 0` and no `--picos`, license CSV is ignored (all_emissions mode)

## Open questions / TODO
- `step2_test_router.py` should be deleted or refactored to use main.py
- No `--output` flag for file output
- No `--verbose` flag for debug output
- No proper test framework (pytest, unittest)
