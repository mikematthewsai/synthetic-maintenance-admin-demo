# Reproducible fixture test plan

**SYNTHETIC DEMONSTRATION. DRAFT. NOT AUTHORIZED FOR MAINTENANCE.**

Run from this project's folder with Python 3.14.0:

```powershell
git rev-parse HEAD
git status --short
python -m unittest discover -s tests -v
python run_evidence.py
```

`output/evidence/results.json` records the exact local commit, Python version, test count/failures/errors, fixture fingerprint, primary pack ID and scenario outputs. `output/evidence/test-results.txt` holds the actual unittest log. Check out that commit locally and rerun the same command to reproduce source and behavior. Elapsed times are not expected to be identical. No dependency download is required. Fixture generation is optional; committed fixture files are the pinned input. Do not regenerate or change them for a pinned evidence run.

## Seeded failures, not unit-test failures

The main J-SYN-100 / P-SYN-101 pack must fail administrative completeness: coordinator missing; planned_date conflicts between November 3 and 4, 2026; admin_status conflicts between draft_ready and deferred. Its source manifest must contain asset-register revision 2 passage p1, job-register revision 2 passage p1 and handover-note revision 1 passage p1. Old register revision 1 and old asset revision 1 cannot fill missing current facts. P-SYN-101A belongs to J-SYN-101 and its coordinator cannot leak into the main pack. Office material is irrelevant. Unreadable binary input and embedded hostile text produce explicit ingestion exceptions and a human-review queue, not silent success.

Review is only a recorded draft examination, never an approval to maintain equipment. A source or checklist change makes the old snapshot stale; its prior review is stale, a fact query abstains, and a new draft is unreviewed. An unsupported safety, isolation, authorization or savings question always abstains. Source-linked HTML must escape text, resolve each exact passage link locally, and include the source-file and passage hashes matching the fixtures.

## Test coverage and deliberate scope

The suite checks the answer key/citations/hashes; superseded and irrelevant exclusion; similar asset separation; missing-fact abstention; visible date/status conflicts; draft handover/queue; unreadable and malicious-source exceptions; unsupported questions; revision-bound review and change invalidation; checklist invalidation; wrong-snapshot rejection; persistence across separate CLI processes; job/equipment/date retrieval; multiple-current ambiguity; duplicate source identity; path escape; missing source; invalid identity/date; unknown pack and invalid search date; escaped source-linked exports and changed-source export rejection; deterministic reruns; malformed manifest; nested source filenames; absence of network libraries in core imports and runtime connection-attempt traps on representative core flows.

Network tests do not constitute an OS firewall audit or prove every possible environment safe. Source-change checking is not atomic with external editors; race conditions, file locks, power loss, corrupt database, large-corpus performance and concurrent users are not production-tested. Detection patterns cover the seeded instruction attack, not all adversarial natural language. No OCR, real document formats, embeddings or language model evaluation exists. No customer data or representative maintenance expertise was validated.

Initial run: 26 tests passed, zero failures/errors. Three additional checks were then added for runtime network attempts, malformed manifests and collision-safe nested source exports. The final pinned run's actual count and result are recorded by `run_evidence.py`; do not infer a pass from a file merely existing.

Correction after independent review: the earlier nested-path test only tested nested filenames and did not establish collision safety for document/revision concatenation. The initial 29-test version had that defect and failed-current ambiguity counting. Current regression fixtures add exact delimiter-colliding pairs, case-sensitive IDs on case-insensitive filesystems, and an unreadable current competitor. Five tests now check distinct exact source exports, simulated duplicate/casefold mapping rejection before writes, and readable-revision exclusion when competitors are unreadable, missing, invalid or quarantined. The suite has 34 tests. Import coverage now includes every import alias and from-import; runtime traps cover socket.connect, connect_ex and create_connection on selected flows, not general network isolation.
