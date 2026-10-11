# Rerun the exported package

SYNTHETIC DEMONSTRATION. DRAFT. NOT AUTHORIZED FOR MAINTENANCE.

Source commit represented by this export: 0b5f39af903ee3fed80ab62031365c681d737fc6. Git internals are deliberately absent. Do not call the exported tree a Git checkout or invent a new commit matching the original. Check each original file against PACKAGE-MANIFEST.json before testing. Source bytes/fixture bytes in the ZIP are the pinned worker files, with LF text handling in .gitattributes.

From the extracted synthetic-maintenance-admin folder, with Python 3.14.0 if available:

```text
python -m unittest discover -s tests -v
python demo.py --db output/consumer.sqlite ingest
python demo.py --db output/consumer.sqlite build --job J-SYN-100 --equipment P-SYN-101 --export output/consumer-view
```

The unit tests exercise persistence/review invalidation with temporary copied fixtures and separate CLI processes. They leave original fixtures unchanged. Any version/environment difference must be recorded with the consumer's actual result. Read fixture-answer-key.json before interpreting success. No pip/network/API/model needed.

run_evidence.py requires a clean Git repository with the source committed; do not use it unchanged on this archive or misrepresent a consumer-created commit as the worker commit. The unittest command above is the reproduction route without Git. If the consumer later initializes its own local review repository, record that new commit separately. Inspect the packaged original output/evidence/results.json and scenarios.json for the worker's pinned report, not as evidence the consumer has rerun them.

Every output remains a synthetic draft. No maintenance/safety/isolation authorization. Open local HTML only through an allowed local reader; respect any browser protocol denial and do not bypass it.
