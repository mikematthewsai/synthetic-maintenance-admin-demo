# Published inspection evidence

**SYNTHETIC DEMONSTRATION. DRAFT. NOT AUTHORIZED FOR MAINTENANCE.**

The owner approved publishing this fictional source and the recorded evidence. No new software license has been added. This publication is an inspection artifact, not an operational service or maintenance approval.

Reviewed and tested implementation commit: [0b5f39af903ee3fed80ab62031365c681d737fc6](https://github.com/mikematthewsai/synthetic-maintenance-admin-demo/tree/0b5f39af903ee3fed80ab62031365c681d737fc6).

Frozen evidence is in [evidence/reviewed-0b5f39a](evidence/reviewed-0b5f39a). The original report records 34 passing tests on Python 3.14.0. A fresh archive extraction also ran 34 tests with zero failures. These were worker runs; independent static review checked the package and found two defects in an earlier version, but did not independently execute the tests or verify maintenance semantics.

- [Actual results](evidence/reviewed-0b5f39a/results.json)
- [Actual test log](evidence/reviewed-0b5f39a/test-results.txt)
- [Extracted-package test log](evidence/reviewed-0b5f39a/package-extraction-test.txt)
- [Draft pack JSON](evidence/reviewed-0b5f39a/primary-draft/draft-pack.json)
- [Draft HTML snapshot](evidence/reviewed-0b5f39a/primary-draft/draft-pack.html)
- [Source-change and abstention scenarios](evidence/reviewed-0b5f39a/scenarios.json)
- [Fixture answer key](fixture-answer-key.json)
- [Capability limits](CAPABILITY-LIMITS.md)

The package manifest retains original paths/hashes from the reviewed export. Original `output/evidence/` files were relocated under `evidence/reviewed-0b5f39a/` without changing their bytes; original `output/cli-*` records are alongside them. Source files refer to the reviewed implementation commit. Local HTML passage links are preserved. Hashes identify a snapshot, not authorship or operational correctness.

To reproduce the exact implementation, check out commit 0b5f39af903ee3fed80ab62031365c681d737fc6 and follow README.md. The latest publication commit adds evidence/documentation only. Real documents, model/RAG/OCR functionality, authenticated review, CMMS integration and operational deployment are absent. This small test corpus does not prove reliability, safety, representative coverage or savings.
