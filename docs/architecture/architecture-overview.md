# Architecture Overview

## 1. Purpose

EventFlow Agent is designed as a stateful Agentic Workflow for SaaS external event triage.

The system takes noisy external signals and turns them into structured risk decisions. The architecture is intentionally workflow-first instead of chatbot-first: each step has a clear responsibility, typed state, routing rules, and testable behavior.

The MVP focuses on generating an Event Risk Brief. Later versions may extend the workflow to controlled action recommendation and approved tool calling.

## 2. System Context

At a high-level, EventFlow Agent sits between external event sources and internal team decisions.

```text
External Signals
  ↓
EventFlow Agent
  ↓
Event Risk Brief
  ↓
Reviewer / Engineering Team / Optional Action Layer
```

External signals may come from:

- status pages;
- release notes;
- security advisories;
- Github releases;
- vendor blogs;
- RSS Feeds;
- manually imported sample data.

Internal context may include:

- dependency map;
- playbooks;
- historical cases;
- risk routing rules;
- human review decisions.

## 3. Design Principles

### Workflow first, not chatbot first

The system is modeled as a workflow with explicit steps, not as an open-ended chat assistant.

### Schema-first state design

Each major object should have a structured schema. This makes the workflow easier to test, inspect, and extend.

### Evidence-backed risk assessment

Risk decisions should be based on source evidence, dependency context, playbooks, and historical cases instead of unsupported model output.

### Human review before risky actions

High-risk, low-confidence, or side-effecting decisions should be routed to human review.

### Offline-first MVP before real-time ingestion

The MVP starts with sample data to keep development reproducible and testable. Real-time ingestion can be added later.

### Action safety before automation

The architecture should support future tool calling, but direct remediation should be controlled by policy checks and human approval.

## 4. High-level Workflow

```text
Raw Signal
  ↓
Normalize Signal
  ↓
Classify Event
  ↓
Deduplicate / Merge
  ↓
Retrieve Evidence
  ↓
Assess Risk
  ↓
Human Review if Needed
  ↓
Generate Event Risk Brief
  ↓
Optional Action Layer
```

## 5. Component Architecture

### 5.1 Source Layer

Loads external signals.

MVP sources:

- sample JSONL files;
- manually created public-style examples.

Future sources:

- RSS feeds;
- GitHub releases;
- status pages;
- security advisory APIs.

### 5.2 Normalization Layer

Converts source-specific input formats into a shared RawSignal schema.

This prevents downstream workflow nodes from depending on source-specific fields.

### 5.3 Event Understanding Layer

Classifies the event and extracts initial structured information.

It answers:

- What type of event is this?
- Which vendor or dependency is involved?
- What is the event summary?
- How confident is the classification?

### 5.4 Deduplication Layer

Groups duplicate or related event candidates.

The MVP can start with deterministic rules such as vendor match, event type match, similar title, and close time window.

Later versions may add embedding similarity or LLM-based merge judgment.

### 5.5 Evidence Retrieval Layer

Retrieves context needed for risk assessment.

Possible evidence sources:

- dependency map;
- playbooks;
- historical cases;
- source references.

This is where Agentic RAG can be introduced. The retrieval layer supports event triage rather than generic Q&A.

### 5.6 Risk Assessment Layer

Assigns risk level, confidence, and recommended action.

Example outputs:

- risk level: low / medium / high / critical;
- confidence score;
- affected dependencies;
- recommended action;
- whether human review is required.

### 5.7 Human Review Layer

Pauses the workflow when a case requires human judgment.

Typical triggers:

- high risk;
- low confidence;
- missing evidence;
- conflicting evidence;
- action with side effects.

Reviewer actions may include approve, reject, edit risk level, request more evidence, or escalate.

### 5.8 Publishing Layer

Generates the final Event Risk Brief.

The brief should be structured, evidence-backed, and readable by engineering, support, or review teams.

### 5.9 Optional Action Layer

Planned for future versions.

Possible actions:

- create a mock issue;
- generate a notification draft;
- update an incident log;
- trigger a diagnostic workflow;
- open a dependency upgrade PR.

Side-effecting actions should require policy checks and human approval.

## 6. LangGraph Workflow Design

LangGraph is used as the workflow orchestration layer.

The planned design uses:

- StateGraph to model the workflow;
- nodes for each processing steps;
- shared typed states across nodes;
- conditional edges for routing decisions;
- interrupt / resume for human review in later stages;
- checkpoint and persistence in later stages;
- replayable runs for evaluation.

The workflow should avoid hidden side effects. Each node should clearly define which state fields it reads, which state fields it writes, and how it handles errors.

## 7. Data Flow

The data flow starts from a Raw Signal and gradually becomes more structured.

```text
RawSignal
  ↓
EventCandidate
  ↓
EventCluster
  ↓
EvidencePack
  ↓
RiskAssessment
  ↓
HumanReviewDecision, if needed
  ↓
EventRiskBrief
```

Detailed schemas should be maintained in `data-model.md`.

## 8. Human-in-the-loop and Action Safety

Human-in-the-loop is a core design requirement, not an optional UI feature.

The system should not automatically execute high-impact actions only because an LLM suggested them. Instead, the workflow should separate:

```text
understanding the event
→ assessing risk
→ recommending action
→ checking tool policy
→ requesting human approval if needed
→ executing controlled action
```

The MVP stops at Event Risk Brief generation. Later versions can add approved tool calling.

## 9. MVP Architecture

The MVP should remain small and reproducible.

```text
Sample Raw Signals
  ↓
Pydantic Schema
  ↓
Rule-based Baseline Nodes
  ↓
LangGraph StateGraph
  ↓
Risk Routing
  ↓
Human Review Simulation
  ↓
Event Risk Brief
```

The MVP does not require:

- live data ingestion;
- production database;
- real alerting tools;
- real remediation;
- complex UI.

## 10. Extension Plan

### V1 - Action Recommendation

Use the Event Risk Brief to recommend next steps such as watch, notify support, create issue, or escalate.

### V2 - Tool Calling with Approval

Add controlled tool calls such as creating a mock issue, generating a notification draft, or triggering a diagnostic workflow.

### V3 - Controlled Remediation

Explore limited remediation workflows such as opening dependency upgrade PRs or running safe playbook steps.

High-risk actions should require human approval.

## 11. Related Documents

- `docs/architecture/README.md` — architecture document index;
- `docs/architecture/data-model.md` — planned schema details;
- `docs/architecture/state-design.md` — planned LangGraph state design;
- `docs/architecture/graph-design.md` — planned workflow graph details;
- `docs/architecture/action-layer.md` — planned future tool calling design;
- `docs/project-roadmap.md` — milestone plan and completion criteria.
