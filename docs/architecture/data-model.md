# Data Model

This document defines the M1 data model contract for EventFlow Agent.

It is a schema design document, not an implementation file. Pydantic models, loaders, sample data, and validation tests should follow this contract.

---

## 1. Purpose

EventFlow Agent processes external SaaS-related signals through a structured workflow:

```text
RawSignal
→ EventCandidate
→ EventCluster
→ EvidencePack
→ RiskAssessment
→ HumanReviewDecision
→ EventRiskBrief
```

The data model exists to make the workflow:

- explicit;
- testable;
- auditable;
- easy to validate;
- safe for future LLM, RAG, Human-in-the-loop, and tool calling features.

M1 focuses on schema design, sample data, validation, and dataset consistency.

---

## 2. Design Principles

### 2.1 Schema-first

Core workflow artifacts should use typed schemas.

Avoid long-lived untyped dictionaries between workflow nodes.

---

### 2.2 Synthetic-data-aware

M1 uses synthetic sample data with public vendor/dependency names.

The data model must explicitly support synthetic records through fields such as `is_synthetic`.

---

### 2.3 Evidence-backed

Risk-related models should preserve evidence references.

Risk decisions should be traceable to source signals, dependency context, playbooks, or historical cases.

---

### 2.4 Workflow-ready

Each model should map to a meaningful workflow stage.

A model should exist because a workflow step needs to read, write, validate, route, evaluate, or display that data.

---

### 2.5 MVP-small, extensible later

M1 should stay small.

Do not add fields only because they may be useful in a future product version. Future versions can extend the schema when needed.

---

## 3. Entity Relationship Overview

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
HumanReviewDecision
  ↓
EventRiskBrief
```

Supporting dataset models:

```text
DependencyMap
Playbook
HistoricalCase
EvalCase
```

Relationship summary:

- `RawSignal` stores the original external signal.
- `EventCandidate` stores the system's first structured interpretation.
- `EventCluster` groups duplicate or related candidates.
- `EvidencePack` stores retrieved context for risk assessment.
- `RiskAssessment` stores risk judgment and routing signals.
- `HumanReviewDecision` stores reviewer decisions.
- `EventRiskBrief` stores the final structured output.
- `DependencyMap`, `Playbook`, and `HistoricalCase` support evidence retrieval.
- `EvalCase` supports replay evaluation.

---

## 4. Shared Enums and Conventions

### 4.1 EventType

M1 supports four event types:

```text
service_incident
security_advisory
api_change
product_release
```

Do not add new event types in M1 unless the roadmap is updated.

Out of scope for M1:

```text
pricing_change
policy_change
vendor_acquisition
compliance_update
market_news
```

---

### 4.2 SourceType

Allowed source types:

```text
status_page
release_note
security_advisory
vendor_blog
github_release
rss
manual
```

M1 sample data may use these source types without implementing real external integrations.

---

### 4.3 RiskLevel

Allowed risk levels:

```text
low
medium
high
critical
```

Definitions:

| Risk Level | Meaning                                                                                                                   |
| ---------- | ------------------------------------------------------------------------------------------------------------------------- |
| `low`      | Informational or low-impact event. Record or observe only.                                                                |
| `medium`   | May affect internal workflows or non-critical capabilities. Watch or notify relevant team.                                |
| `high`     | May affect a core dependency, customer experience, security, or release process. Human review should usually be required. |
| `critical` | May cause major service disruption, severe security risk, or significant customer impact. Escalation is required.         |

---

### 4.4 RecommendedAction

Allowed recommended actions for MVP:

```text
ignore
watch
notify_support
create_internal_issue
escalate_to_engineering
request_more_evidence
```

Out of scope for MVP:

```text
auto_fix
rollback
deploy_hotfix
patch_dependency
restart_service
```

These belong to future controlled remediation versions.

---

### 4.5 ReviewStatus

Allowed review statuses:

```text
not_required
pending
approved
rejected
edited
requested_more_evidence
```

M1 defines the enum. M5 will implement full Human-in-the-loop behavior.

---

### 4.6 ExpectedRoute

Allowed evaluation routes:

```text
auto_brief
human_review
request_more_evidence
error
```

---

## 5. Core Schemas

---

## 5.1 RawSignal

### Purpose

`RawSignal` represents an unprocessed external input.

It stores the original signal before the system classifies, deduplicates, retrieves evidence, or assesses risk.

### Main Fields

| Field          | Type               | Required | Description                                                                 |
| -------------- | ------------------ | -------: | --------------------------------------------------------------------------- |
| `signal_id`    | `str`              |      yes | Unique ID for the raw signal.                                               |
| `source_type`  | `SourceType`       |      yes | Source category, such as `status_page`, `github_release`, or `manual`.      |
| `vendor`       | `str`              |      yes | Public vendor or dependency name, such as `GitHub Actions` or `Stripe API`. |
| `title`        | `str`              |      yes | Signal title.                                                               |
| `content`      | `str`              |      yes | Raw signal content.                                                         |
| `published_at` | `datetime \| None` |       no | Synthetic or source publication time.                                       |
| `source_url`   | `str \| None`      |       no | Null or placeholder URL for synthetic records.                              |
| `metadata`     | `dict`             |       no | Source-specific metadata.                                                   |
| `is_synthetic` | `bool`             |      yes | Must be `true` for M1 sample data.                                          |

### Validation Rules

- `signal_id` must not be empty.
- `title` must not be empty.
- `content` must not be empty.
- `vendor` must not be empty.
- M1 sample records must have `is_synthetic = true`.
- Synthetic records must not use real incident IDs, real CVE IDs, or real status page URLs.
- `source_url` should be `null` or an `example.com`-style placeholder for synthetic records.

### Used By

- sample data validation;
- normalization node;
- event classification node;
- replay evaluation input.

---

## 5.2 EventCandidate

### Purpose

`EventCandidate` represents the system's first structured interpretation of a `RawSignal`.

It is not the final truth. It is a candidate understanding that may later be merged, corrected, reviewed, or rejected.

### Main Fields

| Field                   | Type        | Required | Description                                              |
| ----------------------- | ----------- | -------: | -------------------------------------------------------- |
| `candidate_id`          | `str`       |      yes | Unique candidate ID.                                     |
| `source_signal_id`      | `str`       |      yes | ID of the originating RawSignal.                         |
| `event_type`            | `EventType` |      yes | Classified event type.                                   |
| `vendor`                | `str`       |      yes | Vendor or dependency name.                               |
| `affected_dependencies` | `list[str]` |      yes | Dependencies likely affected by the event.               |
| `summary`               | `str`       |      yes | Short structured summary.                                |
| `confidence`            | `float`     |      yes | Confidence score between 0 and 1.                        |
| `evidence_refs`         | `list[str]` |       no | Source or evidence references supporting this candidate. |

### Validation Rules

- `candidate_id` must not be empty.
- `source_signal_id` must reference a RawSignal when used in sample/eval data.
- `event_type` must be one of the allowed M1 event types.
- `confidence` must be between 0 and 1.
- `summary` must not be empty.

### Used By

- deduplication;
- EventCluster generation;
- evidence retrieval;
- risk assessment;
- evaluation.

---

## 5.3 EventCluster

### Purpose

`EventCluster` represents a group of duplicate or related EventCandidates.

External events often appear as multiple updates, summaries, or follow-up signals. The cluster prevents the workflow from treating every update as a separate event.

### Main Fields

| Field                   | Type               | Required | Description                             |
| ----------------------- | ------------------ | -------: | --------------------------------------- |
| `cluster_id`            | `str`              |      yes | Unique cluster ID.                      |
| `candidate_ids`         | `list[str]`        |      yes | Candidate IDs included in the cluster.  |
| `canonical_title`       | `str`              |      yes | Representative title for the cluster.   |
| `canonical_summary`     | `str`              |      yes | Representative summary for the cluster. |
| `event_type`            | `EventType`        |      yes | Cluster-level event type.               |
| `vendor`                | `str`              |      yes | Main vendor or dependency.              |
| `affected_dependencies` | `list[str]`        |      yes | Dependencies affected by the cluster.   |
| `first_seen_at`         | `datetime \| None` |       no | Earliest signal timestamp.              |
| `last_seen_at`          | `datetime \| None` |       no | Latest signal timestamp.                |
| `confidence`            | `float`            |      yes | Cluster confidence between 0 and 1.     |

### Validation Rules

- `cluster_id` must not be empty.
- `candidate_ids` must not be empty.
- `canonical_title` must not be empty.
- `canonical_summary` must not be empty.
- `confidence` must be between 0 and 1.
- `last_seen_at` should not be earlier than `first_seen_at` when both exist.

### Used By

- deduplication;
- evidence retrieval;
- risk assessment;
- EventRiskBrief generation.

---

## 5.3.1 RetrievalQuery

### Purpose

`RetrievalQuery` stores the structured query used by M4 evidence retrieval.

It is built from an `EventCluster` and keeps retrieval deterministic and testable without an LLM query planner.

### Main Fields

| Field                   | Type        | Required | Description                                      |
| ----------------------- | ----------- | -------: | ------------------------------------------------ |
| `query_id`              | `str`       |      yes | Unique retrieval query ID.                       |
| `event_type`            | `EventType` |      yes | Event type to retrieve evidence for.             |
| `vendor`                | `str`       |      yes | Vendor involved in the event.                    |
| `affected_dependencies` | `list[str]` |       no | Candidate dependency IDs or names.               |
| `keywords`              | `list[str]` |       no | Deterministic keywords extracted from the event. |
| `summary`               | `str`       |      yes | Query summary from the event cluster.            |
| `attempt`               | `int`       |      yes | Retrieval attempt number, starting at 0.         |

---

## 5.4 EvidencePack

### Purpose

`EvidencePack` stores context retrieved to support risk assessment.

It keeps risk judgment separate from evidence collection.

### Main Fields

| Field                      | Type        | Required | Description                                          |
| -------------------------- | ----------- | -------: | ---------------------------------------------------- |
| `evidence_id`              | `str`       |      yes | Unique evidence pack ID.                             |
| `query`                    | `object`    |       no | Structured `RetrievalQuery` used to build evidence.  |
| `source_signal_ids`        | `list[str]` |      yes | Raw signals used as evidence.                        |
| `matched_dependencies`     | `list[str]` |       no | Dependency IDs or names matched from dependency map. |
| `matched_playbooks`        | `list[str]` |       no | Playbook IDs matched for this event.                 |
| `matched_historical_cases` | `list[str]` |       no | Historical case IDs retrieved for context.           |
| `evidence_notes`           | `list[str]` |       no | Short notes explaining evidence relevance.           |
| `missing_evidence_reasons` | `list[str]` |       no | Reasons evidence is weak or insufficient.            |
| `retrieval_quality`        | `float`     |      yes | Retrieval quality score between 0 and 1.             |
| `attempt_count`            | `int`       |      yes | Number of retrieval attempts represented.            |

### Validation Rules

- `evidence_id` must not be empty.
- `retrieval_quality` must be between 0 and 1.
- At least one evidence source should be present unless the workflow is intentionally testing missing evidence.

### Used By

- risk assessment;
- EventRiskBrief generation;
- unsupported fact evaluation;
- replay evaluation.

---

## 5.5 RiskAssessment

### Purpose

`RiskAssessment` stores the system's risk judgment and recommended next action.

It is an internal decision artifact, not the final user-facing brief.

### Main Fields

| Field                   | Type                | Required | Description                                      |
| ----------------------- | ------------------- | -------: | ------------------------------------------------ |
| `risk_level`            | `RiskLevel`         |      yes | Assessed risk level.                             |
| `confidence`            | `float`             |      yes | Risk assessment confidence between 0 and 1.      |
| `risk_factors`          | `list[str]`         |      yes | Factors increasing risk.                         |
| `uncertainty_factors`   | `list[str]`         |       no | Factors reducing confidence or requiring review. |
| `recommended_action`    | `RecommendedAction` |      yes | Suggested next action.                           |
| `requires_human_review` | `bool`              |      yes | Whether review is required.                      |
| `rationale`             | `str`               |      yes | Short explanation of the risk judgment.          |

### Validation Rules

- `risk_level` must be one of the allowed risk levels.
- `recommended_action` must be one of the allowed recommended actions.
- `confidence` must be between 0 and 1.
- `rationale` must not be empty.
- `high` or `critical` events should generally set `requires_human_review = true`.

### Used By

- route decision;
- Human-in-the-loop review;
- EventRiskBrief generation;
- replay evaluation.

---

## 5.6 HumanReviewDecision

### Purpose

`HumanReviewDecision` records reviewer input when the workflow requires human review.

M1 defines this model for future workflow support. Full behavior is implemented in M5.

### Main Fields

| Field                       | Type                        | Required | Description                 |
| --------------------------- | --------------------------- | -------: | --------------------------- |
| `review_id`                 | `str`                       |      yes | Unique review decision ID.  |
| `reviewer_id`               | `str`                       |      yes | Reviewer identifier.        |
| `decision`                  | `ReviewStatus`              |      yes | Review decision.            |
| `edited_risk_level`         | `RiskLevel \| None`         |       no | Optional edited risk level. |
| `edited_recommended_action` | `RecommendedAction \| None` |       no | Optional edited action.     |
| `comments`                  | `str \| None`               |       no | Reviewer comments.          |
| `reviewed_at`               | `datetime \| None`          |       no | Review timestamp.           |

### Validation Rules

- `review_id` must not be empty.
- `reviewer_id` must not be empty when review is performed.
- If `decision = edited`, at least one edited field should be present.
- If `decision = requested_more_evidence`, comments should explain what evidence is missing.

### Used By

- Human-in-the-loop workflow;
- audit log;
- EventRiskBrief generation;
- evaluation of review routing.

---

## 5.7 EventRiskBrief

### Purpose

`EventRiskBrief` is the final structured output of the MVP workflow.

It is not just a summary. It is a decision-support artifact.

### Main Fields

| Field                   | Type                | Required | Description                               |
| ----------------------- | ------------------- | -------: | ----------------------------------------- |
| `brief_id`              | `str`               |      yes | Unique brief ID.                          |
| `title`                 | `str`               |      yes | Brief title.                              |
| `event_type`            | `EventType`         |      yes | Final event type.                         |
| `summary`               | `str`               |      yes | Human-readable event summary.             |
| `affected_dependencies` | `list[str]`         |      yes | Dependencies affected by the event.       |
| `risk_level`            | `RiskLevel`         |      yes | Final risk level.                         |
| `confidence`            | `float`             |      yes | Final confidence score.                   |
| `evidence_refs`         | `list[str]`         |      yes | Evidence references supporting the brief. |
| `risk_rationale`        | `str`               |      yes | Explanation of risk judgment.             |
| `recommended_action`    | `RecommendedAction` |      yes | Recommended next action.                  |
| `review_status`         | `ReviewStatus`      |      yes | Review status.                            |
| `created_at`            | `datetime \| None`  |       no | Brief creation timestamp.                 |

### Validation Rules

- `brief_id` must not be empty.
- `title` must not be empty.
- `summary` must not be empty.
- `confidence` must be between 0 and 1.
- `risk_rationale` must not be empty.
- `evidence_refs` should not be empty unless the workflow is explicitly testing missing evidence.

### Used By

- final MVP output;
- project demo;
- action recommendation in V1;
- tool calling input in V2;
- replay evaluation.

---

## 6. Dataset Support Models

---

## 6.1 DependencyMap

### Purpose

`DependencyMap` defines the simulated SaaS product modules and their external dependencies.

It supports dependency impact analysis.

### Suggested Structure

```text
product_name
modules[]
```

Each module:

```text
module_id
module_name
business_criticality
dependencies[]
```

Each dependency:

```text
dependency_id
vendor
dependency_name
dependency_type
criticality
used_for
```

### Criticality Values

```text
low
medium
high
critical
```

---

## 6.2 Playbook

### Purpose

`Playbook` defines response guidance for event types and dependency criticality.

It supports risk assessment and recommended actions.

### Main Fields

| Field                    | Type                | Required | Description                                |
| ------------------------ | ------------------- | -------: | ------------------------------------------ |
| `playbook_id`            | `str`               |      yes | Unique playbook ID.                        |
| `event_type`             | `EventType`         |      yes | Event type covered by the playbook.        |
| `dependency_criticality` | `RiskLevel`         |      yes | Criticality level the playbook applies to. |
| `risk_level`             | `RiskLevel`         |      yes | Suggested risk level.                      |
| `recommended_action`     | `RecommendedAction` |      yes | Suggested action.                          |
| `review_required`        | `bool`              |      yes | Whether human review is required.          |
| `guidance`               | `str`               |      yes | Human-readable response guidance.          |

---

## 6.3 HistoricalCase

### Purpose

`HistoricalCase` contains synthetic past cases used for future retrieval and evaluation.

### Main Fields

| Field                   | Type                | Required | Description                          |
| ----------------------- | ------------------- | -------: | ------------------------------------ |
| `case_id`               | `str`               |      yes | Unique historical case ID.           |
| `event_type`            | `EventType`         |      yes | Historical event type.               |
| `vendor`                | `str`               |      yes | Vendor involved.                     |
| `affected_dependencies` | `list[str]`         |      yes | Dependencies affected.               |
| `summary`               | `str`               |      yes | Case summary.                        |
| `risk_level`            | `RiskLevel`         |      yes | Historical risk level.               |
| `action_taken`          | `RecommendedAction` |      yes | Action taken in the historical case. |
| `outcome`               | `str`               |      yes | Result of the action.                |
| `lessons_learned`       | `str`               |       no | Notes for future handling.           |
| `is_synthetic`          | `bool`              |      yes | Must be true for sample data.        |

---

## 6.4 EvalCase

### Purpose

`EvalCase` defines labeled evaluation cases for replay evaluation.

Eval labels may be drafted by AI, but they must be reviewed before treated as ground truth.

### Main Fields

| Field                            | Type                | Required | Description                         |
| -------------------------------- | ------------------- | -------: | ----------------------------------- |
| `eval_id`                        | `str`               |      yes | Unique eval case ID.                |
| `input_signal_id`                | `str`               |      yes | RawSignal ID used as input.         |
| `expected_event_type`            | `EventType`         |      yes | Expected event classification.      |
| `expected_affected_dependencies` | `list[str]`         |      yes | Expected affected dependencies.     |
| `expected_risk_level`            | `RiskLevel`         |      yes | Expected risk level.                |
| `expected_route`                 | `ExpectedRoute`     |      yes | Expected workflow route.            |
| `expected_recommended_action`    | `RecommendedAction` |      yes | Expected action.                    |
| `label_rationale`                | `str`               |      yes | Explanation for the expected label. |
| `label_status`                   | `str`               |      yes | `draft` or `reviewed`.              |

### Validation Rules

- `input_signal_id` should reference a RawSignal.
- `label_status` should be `draft` or `reviewed`.
- Eval cases should not be treated as gold labels until reviewed.

---

## 7. ID Conventions

Recommended ID formats:

```text
sig_001
cand_001
cluster_001
evidence_001
brief_001
dep_github_actions
pb_service_incident_high
hist_001
eval_001
```

Rules:

- IDs should be stable.
- IDs should be human-readable.
- IDs should not contain real incident IDs or real CVE IDs in synthetic data.
- IDs should be unique within their file or model type.

---

## 8. Global Validation Rules

M1 validation should enforce:

1. Required fields must not be empty.
2. `confidence` fields must be between 0 and 1.
3. `event_type` must be one of the allowed M1 event types.
4. `risk_level` must be one of the allowed risk levels.
5. `recommended_action` must be one of the allowed actions.
6. M1 sample `RawSignal` records must have `is_synthetic = true`.
7. Synthetic data must not use real incident IDs, real CVE IDs, real status page URLs, or real customer data.
8. `source_url` should be null or an `example.com`-style placeholder for synthetic records.
9. Eval labels should be reviewed before treated as ground truth.
10. High-risk or critical records should be explainable by dependency criticality, playbook guidance, or evidence.

---

## 9. M1 Implementation Scope

M1 should implement:

- Pydantic schemas for the core models;
- schema validation tests;
- sample data file formats;
- sample data loaders;
- validation tests for sample data.

M1 should not implement:

- LangGraph workflow;
- LLM extraction;
- real-time data ingestion;
- vector search;
- full Human-in-the-loop behavior;
- tool calling;
- remediation.

---

## 10. Future Extensions

Future versions may add:

- pricing or policy change event types;
- richer dependency graph modeling;
- source reliability scoring;
- semantic deduplication;
- LLM-based extraction;
- vector retrieval;
- action policy models;
- detailed audit log models;
- production persistence models.

These should be added only when the corresponding roadmap milestone requires them.
