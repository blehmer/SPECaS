---
spec-version: 0.1.0
project: [Project Name]
owner: [Spec Steward / PM]
last-updated: 2025-09-26
---

# 00 Overview
**Intent:** This spec captures the complete, living description of the system.  
**Principles:**  
- Single source of truth, many views.  
- Requirements written as atomic units with stable IDs.  
- Diffs and Spec Change Requests (SCRs) drive evolution.  
- Machine-usable + human-usable = executable spec.  

---

# 10 Domain Model
Describe the problem space in terms of **entities, events, and relationships**.  

Example:
- **Entity:** Document  
- **Attributes:** doc_id, version, annotations  
- **Event:** Re-import document  
- **Constraint:** doc_id is immutable across versions  

---

# 20 Capabilities
List system capabilities at a high level. Each references atomic requirements (`RQ-*`).

**Convention:** Keep any design references **inside the Capability** they belong to. Tools can derive a global map from these per-CAP blocks; humans only update here.
  

**CAP-01: PDF Re-Import**  
Intent: Re-importing a known document updates content without losing user work.  
KPIs: Re-link success P95 ≥ 0.90; ingest time P50 ≤ 3s/page  
Atoms: [RQ-132, RQ-014, ALG-17]  

Visual Aids:
- VA-001:
  Title: Re-Import Flow v3
  Type: figma
  URL: https://www.figma.com/file/<FILE_KEY>?node-id=<NODE_ID>&version-id=<VERSION_ID>
  FileKey: <FILE_KEY>
  NodeId: <NODE_ID>
  Version: v3
  Updated: 2025-09-26
  RelatesTo: [RQ-132, RQ-014]

- VA-002:
  Title: Orphaned Annotation Flow (Decision Diagram)
  Type: flowchart
  Tool: mermaid
  Path: /design/flows/orphaned-annotation.mmd
  Version: v1
  Updated: 2025-09-26
  RelatesTo: [RQ-132]

---

# 30 Requirements
Atomic requirements are the **core unit**. Keep them short, numbered, and stable.  

### RQ-132: Retain Annotations on Re-Import
ID: RQ-132  
Type: Functional  
Scope: Ingestion.PDF  
Status: Proposed  
DependsOn: [RQ-014]
Rationale: Users annotate PDFs; re-imports must not wipe annotations.  

**Spec**  
- When a previously-imported PDF (same doc_id) is re-ingested, the system shall preserve user annotations and re-link them to updated text spans using fuzzy positional matching (algorithm described in "Fuzzy Positional Matching" notes; formal ALG-17 to be added).
**Invariants**  
- annotation.author_id and created_at are immutable.  
- If a target span no longer exists, mark annotation as *orphaned* with reason.  

**Acceptance**
- **Given** a previously imported document `A` with 3 annotations bound to text spans in v1,
  **When** v2 of document `A` is re-imported with content changes,
  **Then** 2 annotations are re-linked to updated spans and 1 is marked *orphaned* with `reason="span_missing"`.
- **Given** any remap operation occurs,
  **When** the re-import completes,
  **Then** the audit log contains an entry for each remap including `old_span`, `new_span`, and `confidence` (≥ 0.78).

**Metrics**  
- Re-link success rate P50 ≥ 0.95, P95 ≥ 0.90 on internal test corpus.  

**TestVectors**  
```json
{ "doc_id": "A", "v1_annotations": [...], "v2_text": "...", "expected": {...} }
```

**Prompts**  
- GEN-CODE: "Implement ALG-17 for fuzzy positional matching using token windows and cosine similarity over embeddings. Honor invariants above."  
- GEN-TESTS: "Create unit and property-based tests for RQ-132 using TestVectors."  

---

### RQ-014: Fuzzy Positional Matching
ID: RQ-014  
Type: Functional  
Scope: Ingestion.PDF  
Status: Proposed  
DependsOn: []  
Rationale: Re-linking annotations across document versions requires robust span matching.

**Spec**
- The system shall compute candidate new spans for each previous annotation using windowed token offsets and embedding similarity.
- If the best match confidence < 0.78, the annotation shall be marked *orphaned* with reason.

**Invariants**
- Matching is deterministic for identical inputs.
- Confidence values are recorded per annotation remap.

**Acceptance**
- **Given** an annotation bound to a table row that shifts by +12 characters in v2, **When** re-import runs, **Then** the annotation is re-linked with `confidence ≥ 0.78`.
- **Given** an annotation whose target text is deleted in v2, **When** re-import runs, **Then** the annotation is marked *orphaned* with `reason="span_missing"`.

**Metrics**
- Median remap latency (P50) ≤ 10 ms per annotation.

**TestVectors**
```json
[
  { "case": "shifted-span", "old_span": [120,140], "new_text": "...", "expected": {"status": "relinked", "confidence": 0.83} },
  { "case": "deleted-span", "old_span": [220,240], "new_text": "...", "expected": {"status": "orphaned", "reason": "span_missing"} }
]
```

**Prompts**
- GEN-CODE: "Implement fuzzy positional matching using token windows and cosine similarity over embeddings."
- GEN-TESTS: "Generate unit/property tests for shifted and deleted spans, asserting confidence and orphaning rules."

### RQ-210: Encrypt Sensitive Data at Rest
ID: RQ-210  
Type: Nonfunctional (Security)  
Scope: Storage.Database  
Status: Proposed  
DependsOn: []  
Rationale: Protecting customer data is critical to meet compliance and reduce risk of breaches.  

**Spec**  
- All customer PII (personally identifiable information) fields shall be encrypted at rest using AES-256.  
- Keys must be managed by a secure KMS (Key Management Service) with automatic rotation every 90 days.  

**Invariants**  
- Encrypted fields cannot be queried without decryption.  
- No plaintext PII may persist longer than process memory lifecycle.  

**Acceptance**
- **Given** any database backup taken after encryption is enabled,
  **When** inspecting stored records,
  **Then** all PII fields appear as ciphertext and are not queryable in plaintext.
- **Given** a valid KMS key and ciphertext of `email`,
  **When** decryption is requested,
  **Then** the plaintext exactly matches the original value.

**Metrics**  
- Key rotation occurs automatically with 100% success rate every 90 days.  
- Unauthorized decryption attempts must be logged within 100 ms.  

**TestVectors**  
```json
{ "field": "email", "plaintext": "user@example.com", "ciphertext": "gibberish...", "kms_key_id": "key-2025-01" }
```

**Prompts**  
- GEN-CODE: "Implement AES-256 encryption for PII fields with integration to KMS. Enforce automatic 90-day key rotation."  
- GEN-TESTS: "Generate tests to confirm encryption at rest, decryption accuracy, and failed decryption logging."  

---

# 40 Quality Attributes
Capture non-functional requirements (performance, reliability, cost, privacy, etc.).  

- **QAT-01: Performance**  
  - Ingest pipeline throughput: ≥ 50 pages/minute at P50.  
  - API latency (95th percentile): ≤ 300 ms for retrieval.  

- **QAT-02: Privacy**  
  - All PII fields hashed with HMAC-SHA256 + salt.  
  - No raw URLs stored.  

---

# 50 Data Contracts
APIs, schemas, messages.  

**API: /import**  
- Request: { doc_id, version, file }  
- Response: { status, errors, annotations[] }  

---

# 60 Test Oracles
Reusable test patterns that validate behavior.  

**Oracle: Annotation Preservation**  
- Input: v1 doc with annotations  
- Action: re-import updated doc  
- Expected: annotations preserved or orphaned with reason  

---

# 70 Risks & Decisions
Architectural decisions, risks, and open questions.  

- **ADR-001: Store annotations separately from document text**  
  - Decision: Improves re-link flexibility, avoids schema coupling.  
- **Risk-004: High false positives in re-linking**  
  - Mitigation: introduce guard threshold ≥ 0.78 similarity.  

---

# 80 Operability
Monitoring, SLOs, alerts, runbooks.  

- **SLO:** 99.9% uptime for ingestion service.  
- **Alert:** Fire if annotation re-link success < 0.85 in rolling 1h window.  

---

# 85 Change Management

All changes proceed via GitHub PRs (“Spec Change Requests”, SCRs).  
Use the PR template at `.github/PULL_REQUEST_TEMPLATE.md`.  
Required approvals: Spec Steward/PM and relevant Tech Leads.  
Merges must pass: spec lint, grader evals for changed atoms, and regression checks.

---

# 90 Appendix & Glossary

## Acronyms

- **ADR** – Architectural Decision Record. Captures a significant technical decision, its context, and consequences.
- **AES** – Advanced Encryption Standard. Here, AES‑256 is used for at‑rest encryption.
- **AI** – Artificial Intelligence. Used to refer to agents/models that consume this spec.
- **ALG** – Algorithm. A numbered algorithm referenced by requirements (e.g., `ALG-17`) that specifies a computation/process.
- **API** – Application Programming Interface. Contracts (endpoints, requests, responses) defined in Data Contracts.
- **CAP** – Capability. A high‑level feature grouping that references specific requirement atoms.
- **CPU** – Central Processing Unit. Used when noting performance/throughput impact.
- **JSON** – JavaScript Object Notation. Format used for TestVectors and examples.
- **KMS** – Key Management Service. Secure service for managing encryption keys and rotation.
- **KPI** – Key Performance Indicator. Business or product‑level success metric.
- **P50 / P95** – Percentile metrics; P50 = median; P95 = 95th‑percentile.
- **PDF** – Portable Document Format.
- **PII** – Personally Identifiable Information.
- **QAT** – Quality Attribute. Nonfunctional requirement category (e.g., performance, privacy, reliability).
- **RQ** – Requirement. The atomic, testable unit of specification (e.g., `RQ-132`).
- **SCR** – Spec Change Request. A structured proposal (diff) to change the spec.
- **SLA** – Service Level Agreement. External/contractual reliability or performance commitment (if applicable).
- **SLO** – Service Level Objective. Internal target for reliability/performance/latency.
- **SemSpec** – Semantic Spec Versioning. Scheme for +patch / +minor / +major version bumps.
- **Eval** – Evaluation. Automated or semi‑automated assessment against Acceptance, Invariants, and Oracles.
- **TV** – Test Vector. Shorthand sometimes used for TestVector.
- **HMAC** – Hash‑based Message Authentication Code (used with SHA‑256 for hashing). 
- **SHA‑256** – Secure Hash Algorithm 256‑bit (used for hashing in privacy requirements).
- **PM** – Product Manager. Spec Steward/owner of ratification.

---

## Glossary

- **Atom** – Smallest unit of spec: `RQ` (requirement), `ALG` (algorithm), or `QAT` (quality attribute). Addressable by stable ID.
- **Capsule** – Reusable spec fragment (e.g., “PII handling invariants”) referenced by multiple atoms.
- **Chain‑of‑Command** – Ratification path for changes: contributor → Spec Steward/PM → relevant technical leads.
- **Doc ID (`doc_id`)** – Stable identifier for a logical document across versions.
- **Grader Model** – An AI evaluator that determines PASS/FAIL against Acceptance criteria and Oracles.
- **Invariant** – A condition that must always hold true for a requirement (e.g., “author_id is immutable”).
- **Oracle (Test Oracle)** – Reusable pattern or rule that decides expected outcomes (Section 60).
- **Prompts** – Machine‑consumable instructions attached to an atom (e.g., `GEN-CODE`, `GEN-TESTS`) for code/test generation.
- **Regression Test** – Re‑execution of prior TestVectors to ensure previously passing behavior hasn’t broken.
- **Reinforcement Loop** – Feedback cycle where eval outcomes (esp. failures) trigger code fixes or spec updates (via SCR).
- **Requirement (Atom)** – See `RQ`. Includes Spec, Invariants, Acceptance, Metrics, TestVectors, Prompts.
- **TestVector** – Structured example inputs/outputs used for both automated tests and grader‑model Evals.
