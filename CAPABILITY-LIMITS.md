# Technical capability and unresolved fit

**SYNTHETIC DEMONSTRATION. DRAFT. NOT AUTHORIZED FOR MAINTENANCE.**

## Exists in this local prototype

The implemented path is manifest and checklist -> strict UTF-8 JSON input validation -> exact job/equipment filtering -> reviewer-designated current revisions -> field grouping with exact source/passage hashes -> unresolved register and human queue -> SQLite snapshot/review -> exact retrieval -> escaped local source-linked HTML. The four fields are asset_description, planned_date, coordinator and admin_status. Job and asset IDs are matched exactly, with no fuzzy asset resolution. Date search matches any asserted planned date, visibly including unresolved conflicts. No date is chosen as approved.

A corpus fingerprint includes the manifest bytes, checklist bytes and hashes of all manifest-listed files, including unreadable/superseded files and missing-file markers. This intentionally conservative policy invalidates a review even after an unrelated corpus change. Review records attach to an exact pack/fingerprint. Freshness is recomputed when loading/querying; a stale snapshot remains available for history but its fact query abstains. New builds are unreviewed. Exported HTML is frozen, visibly labeled as a snapshot and requires CLI freshness checking.

Current-revision ambiguity is counted from manifest assertions before ingestion. An unreadable, missing, malformed or quarantined competing current revision blocks use of that document's readable revision and remains an exception in the human queue. Source exports use the hash of a structured identity pair, not delimiter concatenation. A pre-write duplicate check also compares filename casefolds. Regression coverage includes known delimiter/case collisions; this is not a universal cryptographic or filesystem assurance claim.

SQLite stores administrative draft JSON and reviewer notes using parameterized SQL. There is no LLM, embedding, vector store, RAG, OCR or AI service. No model accuracy was tested. Known embedded-instruction patterns are quarantined in these fixtures; more fundamentally, source text never becomes executable instructions. Arbitrary hostile language detection is not claimed. Untrusted HTML-like field text is escaped in exports. Corpus paths resolving outside the fixture root are rejected.

The quarantine consists of three explicit regular-expression patterns, not a general AI security defense. Query accepts only the four exact field keys. The network checks allowlist all top-level imports (including from-imports and multi-import names) and trap three socket connection entry points during selected demonstrated flows. No connection attempts were observed there; these tests do not establish OS-level network isolation or exhaustive runtime behavior.

## Limits of demonstrated ability

| Question | Answer supported today | What would be needed next |
|---|---|---|
| Can you produce traceable administrative drafts? | This small structured fictional corpus, exact references and abstention are tested locally. | Customer-approved field definitions, document types and representative acceptance set. |
| Can you interpret mine maintenance semantics? | No evidence established. There is no operational reasoning or maintenance procedure in this demo. | A qualified domain reviewer owns semantics, exclusions, source authority and acceptance decisions. |
| Can you safely authorize a job or isolation? | No. The program always outputs authorization NONE and abstains on those questions. | Remain outside this prototype. Any real safety-critical scope needs separate domain governance and assurance, not extrapolation from fixture tests. |
| Can it read PDF scans, tables or handwriting? | No. Only small structured UTF-8 JSON fixture documents. Unreadable input is surfaced. | Supported-format inventory; representative extraction/OCR trials; page/table provenance and confidence/error policies. |
| Is the newest source automatically authoritative? | No. A fixture manifest explicitly designates current revisions. Multiple current entries are excluded and flagged. | Real document-control owner, approval lifecycle, effective dates, source system and supersession rules. |
| Can you resolve asset aliases or conflicting dates? | Exact IDs remain separate; conflicts are shown, never chosen automatically. | Customer-approved identity mapping and conflict-resolution workflow, independently validated. |
| Can it integrate with a CMMS, DMS or mine network? | No integrations implemented or tested. | Actual product/version/API, sandbox access, permissions, field mapping, write restrictions, retries/idempotency, audit and integration acceptance tests. No production credentials needed for this demo. |
| Does human review certify the document? | No. Anyone with filesystem/CLI access can record a fictional draft review. Reviews retain unresolved issues. | Named reviewer authority, authenticated identities, independent source approval, segregation, immutable audit and approved review semantics. |
| Does it securely handle confidential records? | Only fictional local files were used; no external transmission. | Data classification, customer permission, least privilege, storage location, retention/deletion, encryption, backups, incident handling and independent security review. |
| Does it work offline? | Core standard-library CLI has no network dependency and a runtime connection-attempt test passes for demonstrated flows. | Validation on actual managed hardware, offline packaging/update policy, synchronization and disconnected operating process. |
| Is it multiuser or tamper resistant? | No. Single-user CLI and editable files/SQLite. Local hashes detect changes, not trusted authorship. | Access control, transactions around source/review version changes, concurrency tests, signed/immutable audit, lock/version policy. |
| What reliability or savings can you promise? | None from these tests. No representative corpus, measured business baseline, operational load or savings study. | Failure thresholds defined by the customer, realistic dataset and independent evaluation, measured pilot baseline and monitored results. |

## Decisions that cannot be answered by code alone

The customer must name the accountable domain reviewer, the authoritative document-control source and revision rules, required administrative fields, permissible outputs and prohibited decisions. The security owner must approve data access, hosting/offline constraints, roles, retention and incident responsibilities. The operational owner must decide where drafts are reviewed and how source changes invalidate them. Integration scope needs actual system details and sandbox evidence. None of those customer facts can be invented from the public portfolio.

A bounded fit today is a local synthetic prototype or discovery assessment for administrative drafting and provenance. This is insufficient evidence to offer a production mining document system, general RAG/OCR accuracy, operational readiness or safety-related automation. Serious questions above have concrete answers where evidence exists, and explicit requirements where evidence is absent.

## Publication proposal, not executed

After independent review, consider publishing only this fictional corpus, code, answer key, pinned test evidence and limitations as an administration demonstration. Reviewers should confirm every source is fictional, no procedure or real site appears, all visible outputs retain the label, and the public page distinguishes deterministic fixture tests from model or production validation. A new public repository, live portfolio link and any outreach would require later explicit approval. No such actions occurred.
