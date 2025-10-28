# Training Guide: Contributing to the Spec-as-Source in GitHub

## 1. Why This Spec Exists
Traditional specs were either too long (nobody read them) or too short (lacked context). With modern AI tooling, a **structured Markdown spec** can serve as the *single source of truth* for product, design, engineering, QA, and data science.

It's based on a concept that Sean Grove introduced. At its heart is the idea that communicating intent is the most valuable skill when co-creating, especially as complexity increases.

Consider the prompts we write when vibe coding or getting an AI assist while coding. Those prompts encapsulate intent. What if they were structured or codified into a rational spec that thoroughly captures intent? When a coding agent executes your prompt, code effectively becomes the compiled software. Do we keep the compiled code and throw away the source? No!

Think of this new spec concept as the highest-level coding language. It enhances our ability to experiment with more complex ideas. This lets us take leaps forward in innovation by letting us tackle bigger challenges than we could before. When used wisely, it enhances lean software development and reduces risk.

Spec-as-source meant to be:
- **Human-readable** (so teams align on context).  
- **Machine-usable** (so AI agents can generate code, tests, and evals).  
- **Diff-friendly** (so changes can be reviewed like code).  
- **Living** (versioned and updated continuously).
- **The source of truth** for how things *should* and *do* work.


---

## 2. The Structure of `spec.md`
The spec is divided into numbered sections. Think of it as an outline that can grow with your project.  

- **00 Overview** – project intent, principles, ownership  
- **10 Domain Model** – entities, events, constraints  
- **20 Capabilities** – high-level features tied to requirements  
- **30 Requirements** – atomic, testable RQs and ALGs  
- **40 Quality Attributes** – nonfunctional requirements  
- **50 Data Contracts** – APIs, schemas, message formats  
- **60 Test Oracles** – correctness patterns  
- **70 Risks & Decisions** – ADRs, risks, open questions  
- **80 Operability** – SLOs, monitoring, runbooks
- **85 Change Management** – process for evolving the spec  
- **90 Appendix & Glossary** – acronyms and definitions  

Each section may contain sample atoms (like `RQ-132`, `RQ-210`) that should be replaced with your project’s real requirements.  

---

## 3. Change Management via GitHub (SCRs as PRs)

All changes to the spec are handled as **Spec Change Requests (SCRs)** through GitHub pull requests.  

### Branch naming
```bash
git checkout -b scr/{short-id}-{slug}
# e.g. scr/024-relink-alg-tune
```

### PR template
Every PR uses the template at `.github/PULL_REQUEST_TEMPLATE.md`.  
It captures: related RQs, version bump (+patch|+minor|+major), summary, proposed diff, impact, test plan, and approvals.  

### Reviews and approvals
- **CODEOWNERS** requires the Spec Steward (PM) and relevant Tech Leads to approve.  
- Protected branch rules prevent merging without approvals + passing checks.  

### Labels
Use GitHub labels to classify changes:  
- `spec:scr` (all spec PRs)  
- `bump:patch` | `bump:minor` | `bump:major`  
- `area:*` for scope (e.g. `area:ingestion`, `area:security`)  

### CI checks
PRs must pass automated checks:  
- **Linting** – spec structure, IDs, links.  
- **Grader evals** – run grader models against changed atoms.  
- **Regression** – re-run tests for affected scopes.  
- **Version bump sanity** – verify bump type matches diff.  

---

## 4. How the Spec Works (Sean Grove’s Framework)

The spec isn’t just documentation — it’s executable context.
*Just because it's not executable software doesn't mean it's not a plan that can be executed.*

- **Base Policy** – the spec defines what must hold true.  
- **Version Bumps** – patch/minor/major encode behavior changes.  
- **Grader Model** – AI evaluators test outputs against Acceptance/Invariants.  
- **Regression Tests** – past vectors always re-run.  
- **Chain-of-Command** – enforced by CODEOWNERS and review rules.  
- **Reinforcement Loop** – failures either fix code or update the spec.  

---

## 5. Example: Using the Spec to Drive an Eval

1. Take `RQ-210: Encrypt Sensitive Data at Rest`.  
2. Run a grader model with the `TestVectors`.  
3. If it outputs plaintext instead of ciphertext → FAIL.  
4. CI blocks the merge until resolved.  
5. Developer either fixes the code or proposes a new SCR via PR.  

---

## 6. Key Takeaways for Contributors
- Treat `spec.md` like **source code**.
- Every change goes through PR review + CI checks.
- Requirements must be **small, atomic, testable**.
- Always include **Acceptance criteria** + **TestVectors**.
- Let the spec inform design, dev, testing, and evals.
- Conflict? Update the spec or the solution, but bring them into agreement.

---

## 7. Sample prompts for authoring with AI help

**Prompt to create a new spec from scratch:**
```text
1. First, read the documentation (`README.md` and `training.md` and sample `spec.md`)
2. Then, create a new spec in `specs/[PROJECT-NAME]/` called "[PROJECT-NAME]-0.1.0.md". Use the following [CONTEXT / TRANSCRIPT / DICTATION / NOTES] to begin fleshing out the new spec. Extract the important information from the shared context into statements that shall serve as "intent" to be captured in the spec, classify those statements if useful, then ensure that they are represented in the components of a valid spec where applicable. It's okay if not every part of the spec is fleshed out. In those cases where detail is not present, ensure that you follow the correct syntax, but exclude sample content not supported by the new content. Include the important structural sections, but supply a statement to indicate no content when sections are unsupported by the notes. Use today's date as the last-updated date. Today's date is YYYY-MM-DD.
3. Then check that that spec is rational, that is, that it agrees with itself.
4. Finally, ensure that the spec is valid per the sample spec structure and documentation. It's okay if not every part of the spec is fleshed out. In those cases where detail is not present, ensure that you follow the correct syntax, but exclude sample content in those sections of the spec unsupported by the shared context. Include the important structural sections, but supply a statement to indicate no content when sections are unsupported by the dialogue. As part of this step, run `tools/lint_spec.py` on it.

<context>

[context, transcript, dictation, notes]

</context>
```

**Prompt to update an existing spec:**
```text
First, read the documentation (`README.md` and `training.md` and sample `spec.md`)
Then update the spec "[PROJECT-NAME]-n.n.n.md" using the context from the transcript of a dialogue between [NAME 1] ([ROLE]) and [NAME 2] ([ROLE]) below, following these instructions:
1. Extract a set of important, well-articulated intents from the shared context. Classify statements if useful.
2. Update the spec to include the articulated intents. Ensure that those "intents" are represented in the components of the spec where applicable, such that the newly articulated intents take precedence over previously documented intents where conflicts exist or where clarity may be added, and where the most minimal changes are made that ensure rationality and agreement among statements in the spec. Use today's date as the last-updated date. Today's date is YYYY-MM-DD. Determine whether these changes are small corrections (00.00.+1) or minor updates (00.+1.00) or major updates (+1.00.00) and increment the version number accordingly.
3. Then check that that spec is rational, that is, that it agrees with itself.
4. Finally, ensure that the spec is valid per the sample spec structure and documentation. It's okay if not every part of the spec is fleshed out. In those cases where detail is not present, ensure that you follow the correct syntax, but exclude sample content not supported by the new content. Include the important structural sections, but supply a statement to indicate no content when sections are unsupported by the dialogue. As part of this step, run `tools/lint_spec.py` on it.

<transcript>

[Transcript]

</transcript>
```

---

## Acronyms at a Glance

| Acronym | Meaning |
|---------|---------|
| ADR     | Architectural Decision Record |
| AES     | Advanced Encryption Standard |
| AI      | Artificial Intelligence |
| ALG     | Algorithm (e.g., ALG-17) |
| API     | Application Programming Interface |
| CAP     | Capability |
| CPU     | Central Processing Unit |
| JSON    | JavaScript Object Notation |
| KMS     | Key Management Service |
| KPI     | Key Performance Indicator |
| P50/P95 | Percentile metrics (median / 95th) |
| PDF     | Portable Document Format |
| PII     | Personally Identifiable Information |
| QAT     | Quality Attribute |
| RQ      | Requirement |
| SCR     | Spec Change Request |
| SLA     | Service Level Agreement |
| SLO     | Service Level Objective |
| SemSpec | Semantic Spec Versioning |
| Eval    | Evaluation |
| TV      | Test Vector |
| HMAC    | Hash‑based Message Authentication Code |
| SHA‑256 | Secure Hash Algorithm 256‑bit |
| PM      | Product Manager |
