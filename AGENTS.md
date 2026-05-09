# AGENTS.md

This file defines repository-level instructions for Codex when working on EventFlow Agent.

Keep this file concise. Detailed workflow and review rules live in:

- `docs/ai-coding-workflow.md`
- `docs/code-review-checklist.md`

---

## 1. Project Context

EventFlow Agent is a LangGraph-based Agentic Workflow project for SaaS external event triage.

The system converts noisy public external signals into structured Event Risk Briefs with evidence, dependency impact analysis, risk assessment, Human-in-the-loop review, and future controlled action execution.

This is a portfolio-grade engineering project. Do not claim real enterprise deployment, real customer usage, or production metrics unless they actually exist in the repository.

---

## 2. Primary Objective

Build a controlled, testable, and explainable AI Agent workflow.

The project should demonstrate:

- schema-first state design;
- LangGraph workflow orchestration;
- node-level testability;
- conditional routing;
- evidence retrieval / Agentic RAG;
- Human-in-the-loop review;
- audit logging;
- replay evaluation;
- safe boundaries for future tool calling.

This project is not a generic chatbot or news summarizer.

---

## 3. Read First

For non-trivial work, inspect the relevant files before coding.

Always read:

1. `README.md`
2. `docs/project-roadmap.md`
3. `docs/architecture/architecture-overview.md`

For architecture or workflow tasks, also inspect:

- `docs/architecture/state-design.md`
- `docs/architecture/graph-design.md`

For implementation tasks, inspect relevant source files and tests.

For AI coding process rules, inspect:

- `docs/ai-coding-workflow.md`

For review tasks, inspect:

- `docs/code-review-checklist.md`

If a referenced file does not exist yet, create only the minimal placeholder needed for the current task.

---

## 4. Current Development Rule

Follow `docs/project-roadmap.md`.

Do not implement post-MVP features early.

During MVP, avoid:

- real-time ingestion;
- production alerting;
- real Slack / Jira / GitHub writes;
- autonomous remediation;
- production authentication;
- complex UI;
- large-scale vector database integration;
- live web crawling.

---

## 5. Core Engineering Rules

### 5.1 Schema-first

Use Pydantic models for core workflow artifacts.

Avoid passing long-lived untyped dictionaries between workflow nodes.

### 5.2 Baseline before LLM

Prefer deterministic baseline logic before adding LLM calls.

Do not add LLM calls before the relevant baseline behavior exists, unless explicitly requested.

### 5.3 Explicit LangGraph state

LangGraph state must be explicit and testable.

Each node should clearly define:

- state fields read;
- state fields written;
- routing behavior, if any;
- error behavior.

### 5.4 Evidence-backed risk assessment

RiskAssessment should use evidence from dependency context, playbooks, historical cases, or source references.

Avoid unsupported risk claims.

### 5.5 Human approval before side effects

Do not execute side-effecting external actions in MVP.

Future tool calling must follow:

```text
EventRiskBrief
→ Action proposal
→ Policy check
→ Human approval if needed
→ Tool execution
→ Audit log
```

### 5.6 Tests for behavior changes

Any behavior change should include tests unless the task is documentation-only.

Mock LLM calls, external APIs, and future tool calls.

---

## 6. Expected Repository Structure

Expected high-level layout:

```text
README.md
README-zh.md
AGENTS.md
pyproject.toml
.env.example

docs/
  project-roadmap.md
  ai-coding-workflow.md
  code-review-checklist.md
  architecture/
  project-notes/

data/
  samples/
  eval/

src/
  eventflow/
    schemas/
    graph/
    nodes/
    retrieval/
    review/
    evaluation/
    api/
    utils/

tests/
  unit/
  integration/
  eval/
```

Create directories only when the current task requires them.

Do not create unnecessary files.

---

## 7. Commands

Use these commands when configured:

```bash
python -m pytest
python -m pytest tests/unit
python -m pytest tests/integration
python -m ruff check .
python -m ruff format .
python -m mypy src
```

If a command is not configured yet, do not claim it passed.

State that it is not configured and recommend adding it if appropriate.

---

## 8. Documentation Rules

Keep README concise.

Use:

- `docs/architecture/` for architecture;
- `docs/project-roadmap.md` for roadmap;
- `docs/project-notes/` for project notes, interview Q&A, decisions, and feature notes.

Do not paste raw AI-generated notes into documentation.

Rewrite them into concise engineering notes.

Chinese docs may exist as `*-zh.md`.

---

## 9. Definition of Done

A task is done only when:

- the requested scope is satisfied;
- unrelated files are not modified;
- implementation is tested when applicable;
- validation commands are run or clearly explained as not run;
- no fake claims are made;
- known gaps are stated;
- documentation is updated when behavior changes.

For coding tasks, final response should include:

```text
Summary
Files changed
Validation
Known gaps
Next step
```

For planning tasks, final response should include:

```text
Goal
Assumptions
Plan
Out of scope
Open questions, if any
```

---

## 10. Hard Do-not Rules

Do not:

- rewrite large parts of the repo without explicit request;
- implement future roadmap items early;
- add side-effecting tool calls during MVP;
- add LLM calls before baseline logic unless requested;
- bypass Pydantic schemas;
- pass raw dictionaries as long-lived workflow state;
- silently add dependencies;
- commit real secrets;
- use real company or customer data;
- claim production usage;
- claim real metrics without evaluation;
- claim tests passed if not run.
