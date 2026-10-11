# Synthetic pump-job administration demonstration

**SYNTHETIC DEMONSTRATION. DRAFT. NOT AUTHORIZED FOR MAINTENANCE.**

Local, deterministic Python prototype for source-linked administrative draft packs. It demonstrates provenance, unresolved questions, review snapshots and retrieval. It contains fictional records, no maintenance procedures, no safety determination and no work authorization. A fictional administrative fixture reviewer defined the checklist; a real qualified reviewer must define requirements before real maintenance semantics are used.

## What can be inspected

- `fixtures/manifest.json`: stable document IDs, explicit revisions and reviewer-designated current flags. Revision numbers are not interpreted as proof of currency.
- `fixtures/checklist.json`: four administrative fields only.
- `fixture-answer-key.json`: expected values, missing facts, conflicts and exclusions.
- `demo.py`: standard-library validation, exact IDs, source and passage SHA256s, draft pack/handover, SQLite persistence, revision-bound review notes and retrieval.
- `tests/test_demo.py`: adversarial fixture and failure-state tests.
- `CAPABILITY-LIMITS.md`: what this demonstrates and what remains unimplemented or undecided.
- `TEST-PLAN.md`: reproducible commands, actual failures in the seeded documents and acceptance checks.
- `run_evidence.py`: runs tests against the local Git commit and produces labeled results plus inspectable snapshots under `output/`.

## Run locally

Python 3.14.0 was used on Windows. No pip install, API key, model, cloud account or external service is required. Do not place real documents in this project.

```powershell
python -m unittest discover -s tests -v
python run_evidence.py
python demo.py ingest
python demo.py build --job J-SYN-100 --equipment P-SYN-101 --export output/view
```

Open `output/view/draft-pack.html` as a local file. Each value links to an escaped source view at its exact passage, revision and original-file hash; the source JSON snapshot is alongside the view. Export names hash the structured document/revision pair and reject duplicate names before writing, including case-insensitive collisions. The HTML is a frozen export and does not dynamically check freshness. Use `get` or `query` for current source freshness.

PowerShell example for a recorded **draft** review and retrieval:

```powershell
$pack = python demo.py build --job J-SYN-100 --equipment P-SYN-101 | ConvertFrom-Json
python demo.py review --pack $pack.pack_id --fingerprint $pack.fingerprint --reviewer fictional-reviewer --note 'Draft examined; missing coordinator and conflicts remain unresolved.'
python demo.py get --pack $pack.pack_id
python demo.py query --pack $pack.pack_id --field planned_date
python demo.py query --pack $pack.pack_id --field safe_to_operate
python demo.py search --job J-SYN-100 --equipment P-SYN-101 --date 2026-11-03
```

The first query preserves both conflicting dates. The second abstains. A review note never changes missing fields, resolves conflicts or authorizes anything. `run_evidence.py` also changes a copied fixture and shows the old review becoming stale, the stale query abstaining and a replacement draft starting unreviewed. It leaves tracked fixtures unchanged.

Data stays in local fixture files, local SQLite and local exports. This is a single-user CLI; it has no remote server, authentication or connection to operating equipment. Local access is ordinary filesystem access. `output/` is ignored by Git. The repository has no remote and has not been deployed or published.

Passing this small, deliberately designed corpus does not establish representative coverage, safety, savings, production reliability or general document understanding. Every source-asserted administrative value remains a claim from a fixture, not an operational fact.

Independent static review identified two real defects in the original 29-test version: delimiter-concatenated export names could collide, and failed-ingestion current revisions were absent from ambiguity counting. Both are corrected with explicit regression fixtures/tests, including the exact ('a-r1','2') versus ('a','1-r2') case, casefold collisions, and unreadable/missing/invalid/quarantined current competitors. The current suite has 34 tests. Original results are historical, not proof those defects never existed.
