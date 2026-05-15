# State Design

This document defines the workflow state design for EventFlow Agent.

The workflow state is the runtime container used by the LangGraph workflow. It stores the current event processing context, business artifacts, routing signals, structured errors, and lightweight audit entries during one graph run.

---

## 1. Purpose

`EventFlowState` represents the state of one event triage workflow run.

It is responsible for carrying data through the graph:

```text
RawSignal
→ EventCandidate
→ EventCluster
→ EvidencePack
→ RiskAssessment
→ HumanReviewDecision
→ EventRiskBrief
```

The state should make the workflow:

- explicit;
- testable;
- inspectable;
- safe to route;
- easy to debug;
- ready for replay evaluation;
- extensible for future Human-in-the-loop and tool calling features.

---

## 2. Relationship to Data Models

`docs/architecture/data-model.md` defines the business artifacts used by the system.

Examples:

- `RawSignal`
- `EventCandidate`
- `EventCluster`
- `EvidencePack`
- `RiskAssessment`
- `HumanReviewDecision`
- `EventRiskBrief`

This document defines how those artifacts are carried during graph execution.

In short:

```text
Data models define what each artifact is.
State design defines how those artifacts move through the workflow.
```

The recommended implementation approach is:

```text
Pydantic models
→ validate business artifacts

TypedDict state
→ hold graph runtime context
```

---

## 3. Design Principles

### 3.1 State should be explicit

Important workflow data should be represented as named state fields.

Avoid hiding important workflow outputs inside temporary local variables, raw dictionaries, or unstructured strings.

---

### 3.2 Nodes should return partial state updates

Each node should update only the fields it owns.

A node should not rewrite the entire workflow state unless there is a clear reason.

---

### 3.3 Business artifacts should use Pydantic models

Workflow artifacts such as `RawSignal`, `EventCandidate`, `RiskAssessment`, and `EventRiskBrief` should use Pydantic models.

The state itself can be a `TypedDict`, but the objects inside the state should be validated business models.

---

### 3.4 Routing state should be separated from business judgment

`RiskAssessment` provides risk signals.

`route_decision` records the selected workflow route.

The routing function is responsible for deciding the final route based on state fields such as:

- `errors`
- `evidence_pack`
- `matched_playbook`
- `risk_assessment`

---

### 3.5 Errors and audit logs should be append-only

`errors` and `audit_log` should preserve the workflow history.

Nodes should append new entries instead of replacing previous entries.

---

### 3.6 Current implementation should stay small

The current workflow should avoid production-only fields such as:

- real tool call records;
- Slack/Jira/GitHub IDs;
- production tenant IDs;
- remediation plans;
- deployment state;
- full tracing payloads.

These can be introduced in later versions when needed.

---

## 4. State Overview

A possible state shape:

```python
from typing import Any, TypedDict

class EventFlowState(TypedDict, total=False):
    # Identity
    run_id: str

    # Business artifacts
    raw_signal: RawSignal
    event_candidate: EventCandidate
    event_cluster: EventCluster
    evidence_pack: EvidencePack
    matched_playbook: Playbook
    risk_assessment: RiskAssessment
    human_review_decision: HumanReviewDecision
    event_risk_brief: EventRiskBrief

    # Routing
    route_decision: RouteDecision

    # Runtime tracking
    errors: list[WorkflowError]
    audit_log: list[AuditLogEntry]
    metrics: dict[str, Any]
```

`total=False` or optional fields are appropriate because not all fields exist at graph start.

For example:

- `raw_signal` exists at workflow input.
- `event_candidate` exists after classification.
- `risk_assessment` exists after risk assessment.
- `event_risk_brief` exists after brief generation.

---

## 5. State Fields

---

## 5.1 Identity Fields

### `run_id`

Purpose:

- identifies one workflow run;
- useful for debugging, logs, tests, and replay evaluation.

Written by:

- workflow entrypoint or graph invocation wrapper.

Read by:

- logging utilities;
- evaluation runner;
- tests.

Missing behavior:

- should be generated before graph execution when possible;
- missing `run_id` should not block core workflow execution in local MVP mode, but should be logged as a warning if used by audit logic.

---

### `thread_id`

Current status:

- future persistence field;
- not required for the current workflow.

Purpose in future versions:

- supports checkpoint persistence;
- supports interrupt/resume behavior;
- connects Human-in-the-loop review to a specific workflow run.

---

## 5.2 Business Artifact Fields

### `raw_signal`

Purpose:

- stores the original external signal that enters the workflow.

Written by:

- graph input.

Read by:

- `normalize_signal_node`;
- `classify_event_node`.

Missing behavior:

- workflow should append a structured error;
- route should become `error`.

---

### `event_candidate`

Purpose:

- stores the first structured interpretation of the raw signal.

Written by:

- `classify_event_node`.

Read by:

- `deduplicate_event_node`.

Missing behavior:

- downstream deduplication should not continue;
- workflow should append a structured error;
- route should become `error`.

---

### `event_cluster`

Purpose:

- stores the deduplicated or grouped event representation.

Written by:

- `deduplicate_event_node`.

Read by:

- `retrieve_evidence_node`;
- `generate_event_risk_brief_node`.

Current behavior:

- minimal single-candidate cluster is acceptable for the current workflow.

Missing behavior:

- evidence retrieval should not continue;
- workflow should append a structured error;
- route should become `error`.

---

### `evidence_pack`

Purpose:

- stores retrieved context used for risk assessment.

Written by:

- `retrieve_evidence_node`.

Read by:

- `assess_risk_node`;
- `route_after_evidence`;
- `generate_event_risk_brief_node`.

Missing behavior:

- distinguish between retrieval failure and insufficient evidence.

Important distinction:

```text
retrieval failure
→ workflow error

retrieval succeeded but evidence is weak
→ request_more_evidence route
```

---

### `matched_playbook`

Purpose:

- stores the playbook selected during M3 rule-based evidence retrieval.

Written by:

- `retrieve_evidence_node`.

Read by:

- `route_after_evidence`;
- `assess_risk_node`.

Current behavior:

- missing playbook after retrieval is treated as insufficient evidence, not a fatal workflow error.

---

### `risk_assessment`

Purpose:

- stores risk level, confidence, risk factors, recommended action, and human review signal.

Written by:

- `assess_risk_node`.

Read by:

- `route_after_risk`;
- `human_review_placeholder_node`;
- `generate_event_risk_brief_node`.

Missing behavior:

- routing cannot proceed normally;
- workflow should append a structured error;
- route should become `error`.

---

### `human_review_decision`

Purpose:

- stores reviewer decision after a real Human-in-the-loop step.

Current behavior:

- not written by the current workflow;
- may be absent or `None`.

Future behavior:

- written by a real review node after interrupt/resume.

Important rule:

- a placeholder node must not create a fake `HumanReviewDecision`.

---

### `event_risk_brief`

Purpose:

- stores the final structured workflow output.

Written by:

- `generate_event_risk_brief_node`.

Read by:

- final output;
- tests;
- future action recommendation layer.

Missing behavior:

- acceptable for `error` route;
- acceptable for `request_more_evidence` route;
- not acceptable for successful `auto_brief` route.

---

## 5.3 Routing Fields

### `route_decision`

Purpose:

- records the selected workflow route.

Allowed values:

```text
auto_brief
human_review
request_more_evidence
error
```

Written by:

- route decision node or route destination node;
- may also be mirrored from conditional routing results for observability.

Read by:

- tests;
- final output inspection;
- audit logic;
- evaluation.

Important rule:

```text
RiskAssessment provides route signals.
route_after_evidence and route_after_risk determine the final route.
route_decision records the final route.
```

---

## 5.4 Runtime Tracking Fields

### `errors`

Purpose:

- stores structured fatal workflow errors.

Written by:

- any node that detects a workflow-level failure.

Read by:

- routing function;
- error handler;
- tests;
- evaluation.

Update behavior:

- append-only.

Important distinction:

- insufficient evidence should use `route_decision = request_more_evidence` and an audit warning;
- `errors` should be reserved for broken workflow execution, such as missing required state.

---

### `audit_log`

Purpose:

- stores lightweight workflow trace entries.

Used for:

- debugging;
- route inspection;
- replay analysis;
- verifying node execution in tests.

Update behavior:

- append-only.

---

### `metrics`

Purpose:

- stores lightweight runtime metrics.

Current status:

- optional.

Possible current fields:

```text
node_count
error_count
final_route
```

Future possible fields:

```text
latency_ms
token_usage
retrieval_score
human_review_rate
```

---

## 6. Field Ownership

| State Field             | Written By                                      | Read By                                                                                          |
| ----------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `run_id`                | workflow entrypoint                             | audit utilities, tests, evaluation                                                               |
| `raw_signal`            | graph input                                     | `normalize_signal_node`, `classify_event_node`                                                   |
| `event_candidate`       | `classify_event_node`                           | `deduplicate_event_node`                                                                         |
| `event_cluster`         | `deduplicate_event_node`                        | `retrieve_evidence_node`, `generate_event_risk_brief_node`                                       |
| `evidence_pack`         | `retrieve_evidence_node`                        | `route_after_evidence`, `assess_risk_node`, `generate_event_risk_brief_node`                     |
| `matched_playbook`      | `retrieve_evidence_node`                        | `route_after_evidence`, `assess_risk_node`                                                       |
| `risk_assessment`       | `assess_risk_node`                              | `route_after_risk`, `human_review_placeholder_node`, `generate_event_risk_brief_node`            |
| `human_review_decision` | future review node                              | `generate_event_risk_brief_node`                                                                 |
| `event_risk_brief`      | `generate_event_risk_brief_node`                | final output, tests, future action layer                                                         |
| `route_decision`        | route decision logic or route destination nodes | tests, final output, evaluation                                                                  |
| `errors`                | any node                                        | routing function, error handler, tests                                                           |
| `audit_log`             | all major nodes                                 | debugging, replay analysis, tests                                                                |
| `metrics`               | graph wrapper or nodes                          | evaluation, tests                                                                                |

Field ownership should remain stable.

A node should not modify fields owned by another node unless explicitly documented.

---

## 7. Routing State

Routing is based on workflow state.

The route function should inspect:

- `errors`
- `evidence_pack`
- `matched_playbook`
- `risk_assessment`

Recommended evidence routing order:

```text
if errors exist:
    error

else if evidence_pack is missing, retrieval quality is too low, or matched_playbook is missing:
    request_more_evidence

else:
    continue_to_assess
```

Recommended risk routing order:

```text
if errors exist:
    error

else if risk_assessment is missing:
    error

else if risk_assessment.requires_human_review is true:
    human_review

else:
    auto_brief
```

The retrieval quality threshold should be configurable.

A default threshold can be introduced in implementation, for example:

```text
retrieval_quality < 0.5
→ request_more_evidence
```

The route function should not mutate state unless implemented as a dedicated route decision node.

---

## 8. Error State

`WorkflowError` should be lightweight and structured.

Suggested fields:

```text
error_id
node_name
error_code
message
input_refs
severity
```

Suggested severity values:

```text
warning
error
critical
```

Suggested error codes:

```text
missing_required_state
invalid_state
classification_failed
deduplication_failed
evidence_lookup_failed
risk_assessment_failed
brief_generation_failed
```

Important distinction:

```text
Workflow error:
The workflow could not perform a required step.

Insufficient evidence:
The workflow ran, but evidence is not strong enough for a confident decision.
```

These should not be treated as the same condition.

For M3, missing dependency or missing playbook evidence should terminate on the `request_more_evidence` route with an audit warning and no normal `EventRiskBrief`.

---

## 9. Audit Log State

`AuditLogEntry` should be lightweight and structured.

Suggested fields:

```text
timestamp
node_name
event
status
message
input_refs
output_refs
route_decision
error_code
```

Allowed status values:

```text
success
warning
error
```

Example:

```json
{
  "timestamp": "2026-05-13T10:30:00Z",
  "node_name": "assess_risk",
  "event": "risk_assessed",
  "status": "success",
  "message": "Risk assessed as high because the event affects a high-criticality dependency.",
  "input_refs": ["cluster_001", "evidence_001"],
  "output_refs": ["risk_001"],
  "route_decision": "human_review",
  "error_code": null
}
```

Audit log should not store:

- full prompts;
- hidden reasoning;
- large raw content;
- secrets;
- real customer data;
- large tool payloads.

The audit log is not a full observability platform. It is a lightweight workflow trace.

---

## 10. State Update Rules

### 10.1 Nodes return partial updates

Nodes should return only the state fields they update.

Example:

```python
return {
    "event_candidate": candidate,
    "audit_log": [new_log_entry],
}
```

---

### 10.2 Business artifacts have owner nodes

A business artifact should usually be written by one owner node.

Examples:

- `event_candidate` is written by `classify_event_node`.
- `event_cluster` is written by `deduplicate_event_node`.
- `risk_assessment` is written by `assess_risk_node`.
- `event_risk_brief` is written by `generate_event_risk_brief_node`.

---

### 10.3 Append-only fields must not be overwritten

`errors` and `audit_log` should be append-only.

Implementation should use either:

- reducer-based append behavior;
- helper functions that preserve existing entries.

Nodes must not accidentally replace previous errors or audit entries.

---

### 10.4 Downstream nodes must check preconditions

A node should check that required upstream fields exist.

For example:

- `deduplicate_event_node` requires `event_candidate`.
- `retrieve_evidence_node` requires `event_cluster`.
- `assess_risk_node` requires `event_cluster` and `evidence_pack`.
- `generate_event_risk_brief_node` requires `event_cluster`, `evidence_pack`, and `risk_assessment`.

Missing required state should produce a structured error.

---

### 10.5 Route function is the final authority

`RiskAssessment.requires_human_review` is a signal.

The route function determines the final route.

This prevents conflicts between business judgment and workflow routing.

---

### 10.6 Error route should not generate a normal brief

If the workflow reaches the `error` route, it should not generate a normal `EventRiskBrief`.

The state should contain:

- `route_decision = error`;
- populated `errors`;
- no normal `event_risk_brief`.

---

### 10.7 Review placeholder should not fake review

The review placeholder can record that a case requires review.

It should not create a `HumanReviewDecision`, because no real reviewer has acted.

Recommended behavior:

```text
route_decision = human_review
review_status = pending
human_review_decision = absent or None
```

---

## 11. Current Scope and Future Extensions

### Current Scope

The current state design supports:

- TypedDict workflow state;
- Pydantic business artifacts;
- route decisions;
- structured errors;
- lightweight audit entries;
- human review placeholder;
- sample lookup evidence retrieval.

### Future Extensions

Future versions may add:

- `thread_id`;
- checkpoint persistence;
- real interrupt/resume;
- full Human-in-the-loop review payloads;
- tool call records;
- action policy state;
- richer metrics;
- LangSmith trace metadata;
- production audit fields.

These should be introduced only when the corresponding feature requires them.
