# Project Roadmap

This document defines the development roadmap for EventFlow Agent.

It is not a generic TODO list. It is a development contract that keeps the project small, testable, and aligned with the goal of building a clear AI Agent engineering portfolio project.

---

## 1. Purpose

EventFlow Agent is a LangGraph-based Agentic Workflow project for SaaS external event triage.

The project simulates how a SaaS team handles noisy public external signals such as service incidents, security advisories, API changes, and product releases.

This roadmap exists to:

- control project scope;
- prevent premature complexity;
- guide AI-assisted coding;
- keep MVP development focused;
- make each milestone testable;
- produce interview-ready engineering artifacts.

---

## 2. Roadmap Guardrails

These guardrails apply across all milestones.

### 2.1 Workflow first, not chatbot first

EventFlow Agent should be designed as a stateful workflow, not a free-form chatbot.

The core workflow is:

```text
Raw Signal
→ Normalize
→ Classify
→ Deduplicate
→ Retrieve Evidence
→ Assess Risk
→ Human Review if Needed
→ Generate Event Risk Brief
→ Optional Action Layer
```

### 2.2 Schema first

Core workflow artifacts should use typed schemas before complex logic is added.

Important schemas include:

- RawSignal
- EventCandidate
- EventCluster
- EvidencePack
- RiskAssessment
- HumanReviewDecision
- EventRiskBrief

### 2.3 Baseline before LLM

Start with deterministic baseline logic before adding LLM, RAG, or tool calling.

This keeps the system testable and prevents the project from becoming a prompt-only demo.

### 2.4 Evidence before judgment

Risk assessment should be supported by dependency context, playbooks, historical cases, and source references.

The system should avoid unsupported risk claims.

### 2.5 Human approval before side effects

The MVP should not execute real external actions.

Future tool calling should be gated by risk level, confidence, policy checks, and human approval when needed.

### 2.6 Evaluation before feature breadth

The project should prioritize measurable workflow quality over adding many integrations.

Useful metrics may include:

- event type accuracy;
- deduplication precision;
- risk route accuracy;
- human review trigger recall;
- unsupported fact rate;
- workflow success rate.

---

## 3. Milestone Overview

| Milestone | Goal                                 | Primary Value                                           |
| --------- | ------------------------------------ | ------------------------------------------------------- |
| M0        | Project Setup & Design Contract      | Clear scope, docs, repo structure, AI coding guardrails |
| M1        | Data Model & Sample Dataset          | Typed schemas and reproducible sample data              |
| M2        | Rule-based Baseline Workflow         | Deterministic workflow before LLM complexity            |
| M3        | LangGraph Workflow MVP               | Stateful workflow, nodes, edges, routing                |
| M4        | Evidence Retrieval / Agentic RAG     | Context-backed risk assessment                          |
| M5        | Human-in-the-loop Review             | Safe review flow for risky decisions                    |
| M6        | Replay Evaluation & Portfolio Polish | Evaluation, documentation, interview readiness          |
| V1        | Action Recommendation                | Recommend next actions from Event Risk Brief            |
| V2        | Tool Calling with Approval           | Execute controlled tool calls after approval            |
| V3        | Controlled Remediation               | Limited safe remediation workflows                      |

---

## 4. MVP Milestones

---

## M0 - Project Setup & Design Contract

### Goal

Create the initial project structure, documentation, architecture boundaries, and AI coding guardrails.

M0 is about making the project controlled and explainable before implementation begins.

### Scope

In scope:

- README;
- architecture overview;
- architecture docs index;
- project roadmap;
- project notes structure;
- AI coding guardrails;
- initial Python project structure;
- sample data placeholders;
- smoke test.

Out of scope:

- LangGraph implementation;
- real external API ingestion;
- full RAG pipeline;
- real tool calling;
- front-end UI;
- production database;
- production deployment.

### Deliverables

- `README.md`
- `README-zh.md`
- `docs/architecture/README.md`
- `docs/architecture/architecture-overview.md`
- `docs/project-roadmap.md`
- `docs/project-notes/`
- `AGENTS.md`
- `docs/ai-coding-workflow.md`
- `docs/code-review-checklist.md`
- `pyproject.toml`
- `src/eventflow/__init__.py`
- `tests/unit/test_smoke.py`
- `data/samples/`

### Completion Criteria

M0 is complete when:

- the project purpose is clear;
- README explains the project without excessive detail;
- architecture overview explains the system at a high level;
- roadmap defines M1-M6 and post-MVP versions;
- AI coding rules are written;
- Python project structure exists;
- a smoke test can run;
- the next step is clearly M1.

### Interview Value

M0 demonstrates that the project is planned like an engineering project, not improvised as a prompt demo.

---

## M1 - Data Model & Sample Dataset

### Goal

Define the core schemas and prepare a reproducible sample dataset.

### Scope

In scope:

- Pydantic schemas;
- sample raw external signals;
- sample dependency map;
- sample playbooks;
- sample historical cases;
- basic evaluation cases;
- schema validation tests.

Supported event types for the first version:

- `service_incident`
- `security_advisory`
- `api_change`
- `product_release`

Out of scope:

- real-time ingestion;
- external API clients;
- vector database;
- LLM extraction;
- complex deduplication;
- real enterprise data.

### Deliverables

- `src/eventflow/schemas/`
- `data/samples/raw_signals.jsonl`
- `data/samples/dependency_map.json`
- `data/samples/playbooks.jsonl`
- `data/samples/historical_cases.jsonl`
- `data/eval/eval_cases.jsonl`
- schema validation tests

### Completion Criteria

M1 is complete when:

- all core schemas are defined with Pydantic;
- sample data can be loaded and validated;
- invalid sample records fail validation;
- at least 20-30 raw signals exist;
- each supported event type has sample examples;
- tests cover schema validation.

### Interview Value

M1 demonstrates schema-first design, data modeling, and reproducible test data preparation.

---

## M2 - Rule-based Baseline Workflow

### Goal

Build a deterministic baseline workflow without relying on LLM behavior.

This baseline becomes the reference point for later LangGraph, RAG, and LLM improvements.

### Scope

In scope:

- load RawSignal;
- normalize signal;
- classify event type using rules;
- match dependency map;
- retrieve relevant playbook using rules;
- assess risk using simple scoring;
- generate EventRiskBrief draft;
- unit tests for each step.

Out of scope:

- LangGraph;
- LLM calls;
- embedding retrieval;
- human review interruption;
- real tool calling;
- complex UI.

### Deliverables

- `src/eventflow/baseline/`
- `src/eventflow/nodes/normalize.py`
- `src/eventflow/nodes/classify_rule_based.py`
- `src/eventflow/nodes/retrieve_playbook_rule_based.py`
- `src/eventflow/nodes/assess_risk_rule_based.py`
- `src/eventflow/nodes/generate_brief.py`
- unit tests for baseline nodes
- CLI or script to run one sample event through the baseline

### Completion Criteria

M2 is complete when:

- one RawSignal can be processed end-to-end;
- the system outputs an EventRiskBrief;
- each baseline step is unit tested;
- at least 3 event types are covered in tests;
- unsupported or malformed input produces structured errors;
- baseline behavior is documented.

### Interview Value

M2 demonstrates deterministic control, testability, and engineering discipline before introducing Agentic complexity.

---

## M3 - LangGraph Workflow MVP

### Goal

Convert the baseline workflow into a LangGraph StateGraph.

LangGraph should add explicit state transitions, conditional routing, and testable workflow paths.

### Scope

In scope:

- LangGraph StateGraph;
- shared workflow state;
- node-level functions;
- conditional routing;
- route decision logging;
- integration tests for graph paths.

Core graph:

```text
START
→ normalize_signal
→ classify_event
→ deduplicate_event
→ retrieve_evidence
→ assess_risk
→ route_review
→ generate_event_risk_brief
→ END
```

Out of scope:

- production persistence;
- real checkpoint/resume;
- full human review UI;
- live integrations;
- complex RAG.

### Deliverables

- `src/eventflow/graph/state.py`
- `src/eventflow/graph/builder.py`
- `src/eventflow/graph/routes.py`
- `tests/integration/test_eventflow_graph.py`
- updated architecture docs
- graph path tests

### Completion Criteria

M3 is complete when:

- LangGraph workflow can process a sample RawSignal;
- state fields are typed and documented;
- node read/write behavior is clear;
- conditional routing is tested;
- at least these paths are covered:
  - low-risk event → auto brief;
  - high-risk event → review route placeholder;
  - invalid event → structured error;
- README or docs show the workflow diagram.

### Interview Value

M3 demonstrates LangGraph StateGraph, structured state, node design, conditional edges, and workflow testing.

---

## M4 - Evidence Retrieval / Agentic RAG

### Goal

Add evidence retrieval over dependency context, playbooks, and historical cases.

RAG is introduced to support event triage and risk assessment, not generic Q&A.

### Scope

In scope:

- retrieve dependency context;
- retrieve matching playbooks;
- retrieve similar historical cases;
- attach evidence references to EventRiskBrief;
- compute basic retrieval quality signals;
- handle missing evidence explicitly.

Out of scope:

- large-scale vector database tuning;
- production semantic search;
- real-time indexing;
- multi-source web crawling;
- fully autonomous query planning.

### Deliverables

- `src/eventflow/retrieval/`
- `src/eventflow/nodes/retrieve_evidence.py`
- `src/eventflow/nodes/evaluate_evidence.py`
- retrieval tests
- evidence-backed risk assessment tests
- sample historical cases

### Completion Criteria

M4 is complete when:

- evidence retrieval is integrated into the graph;
- EventRiskBrief includes evidence references;
- risk assessment uses retrieved evidence;
- retrieval failure is handled explicitly;
- tests cover missing evidence and successful evidence retrieval;
- docs explain where RAG fits.

### Interview Value

M4 demonstrates Agentic RAG, evidence-backed decision-making, retrieval quality handling, and separation between generation and grounding.

---

## M5 - Human-in-the-loop Review

### Goal

Add human review for high-risk, low-confidence, or evidence-insufficient cases.

### Scope

In scope:

Human review routing for:

- high risk;
- low confidence;
- missing evidence;
- conflicting evidence;
- future side-effecting action proposals.

Reviewer actions:

- approve;
- reject;
- edit risk level;
- request more evidence;
- escalate.

MVP implementation may use CLI or API simulation instead of a full UI.

Out of scope:

- complex reviewer dashboard;
- production auth;
- real ticketing integration;
- real notification integration;
- real side-effecting action execution.

### Deliverables

- `src/eventflow/review/`
- `src/eventflow/nodes/human_review.py`
- updated `src/eventflow/graph/routes.py`
- review decision schema
- tests for review routing
- tests for reviewer decision handling

### Completion Criteria

M5 is complete when:

- high-risk cases route to review;
- low-risk cases can bypass review;
- reviewer decisions are recorded;
- route decisions are audit logged;
- request-more-evidence path is represented;
- tests cover approve, reject, and request-more-evidence behavior.

### Interview Value

M5 demonstrates safe Agent design, Human-in-the-loop, risk-aware routing, and production-oriented control boundaries.

---

## M6 - Replay Evaluation & Portfolio Polish

### Goal

Add replay evaluation and polish the project for portfolio and interview use.

### Scope

In scope:

- load eval dataset;
- run workflow over eval cases;
- compute metrics;
- compare baseline vs graph workflow;
- document failure cases;
- update README and architecture docs;
- add example EventRiskBrief outputs;
- update project notes and resume bullets.

Metrics may include:

- event type accuracy;
- deduplication precision;
- risk route accuracy;
- human review trigger recall;
- unsupported fact rate;
- workflow success rate.

Out of scope:

- production analytics;
- long-running monitoring;
- real customer metrics;
- advanced A/B testing.

### Deliverables

- `src/eventflow/evaluation/`
- `data/eval/eval_cases.jsonl`
- `docs/evaluation/eval-plan.md`
- `docs/evaluation/eval-report.md`
- updated README
- updated project notes
- example outputs

### Completion Criteria

M6 is complete when:

- replay evaluation can run on eval cases;
- metrics are reported;
- at least 3 failure cases are documented;
- README includes a clear demo path;
- project notes include interview-ready explanations;
- resume bullets are based on implemented features, not planned features.

### Interview Value

M6 demonstrates evaluation discipline, observability thinking, failure analysis, and portfolio readiness.

---

## 5. Post-MVP Versions

Post-MVP versions should not be implemented during MVP unless explicitly requested.

---

## V1 - Action Recommendation

### Goal

Use the EventRiskBrief to recommend controlled next actions.

Example actions:

- ignore;
- watch;
- notify support;
- create issue;
- escalate to engineering;
- request more evidence.

### Safety Boundary

V1 recommends actions but does not execute external tool calls.

---

## V2 - Tool Calling with Approval

### Goal

Add controlled tool calls after policy checks and approval.

Example tool calls:

- create a mock issue;
- generate a Slack or email draft;
- update an incident log;
- trigger a diagnostic workflow.

### Safety Boundary

Side-effecting actions should require approval unless they are explicitly low risk and reversible.

---

## V3 - Controlled Remediation

### Goal

Explore limited remediation workflows.

Example workflows:

- open a dependency upgrade PR;
- trigger a safe runbook step;
- run a diagnostic workflow;
- create a rollback proposal.

### Safety Boundary

The system should not directly modify production infrastructure.

High-risk remediation must require human approval.

---

## 6. Roadmap Rationale

The roadmap intentionally delays complex AI features.

The order is:

```text
Docs and boundaries
→ schemas and sample data
→ deterministic baseline
→ LangGraph workflow
→ evidence retrieval
→ human review
→ replay evaluation
→ controlled action layer
```

This order is chosen because:

- schemas make workflow state testable;
- baseline logic prevents prompt-only implementation;
- LangGraph adds value after the workflow is clear;
- evidence retrieval improves risk decisions after state exists;
- human review adds safety before tool execution;
- evaluation makes improvements measurable;
- tool calling is safer after risk routing and approval exist.

---

## 7. Non-goals

The roadmap explicitly avoids:

- building a generic news summarizer;
- starting with autonomous remediation;
- using LLMs for every decision;
- adding many data sources too early;
- implementing UI before workflow logic;
- claiming production usage without real deployment;
- claiming real business metrics without real users;
- allowing AI coding tools to rewrite large parts of the project without scope control.

---

## 8. Current Next Step

The next milestone after M0 is:

```text
M1 - Data Model & Sample Dataset
```

M1 should begin only after:

- README is stable;
- architecture overview is stable;
- project roadmap exists;
- AGENTS.md exists;
- AI coding workflow rules exist;
- Python project skeleton exists.
