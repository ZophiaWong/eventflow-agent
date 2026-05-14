# Graph Design

This document defines the LangGraph workflow design for EventFlow Agent.

It describes the graph structure, node responsibilities, edge design, routing behavior, error handling path, review placeholder behavior, and test strategy.

---

## 1. Purpose

EventFlow Agent models external SaaS event triage as a stateful workflow.

The graph takes a `RawSignal` and produces either:

- an `EventRiskBrief`;
- a pending review result;
- a request for more evidence;
- a structured error path.

The graph is designed to make event triage explicit, testable, and extensible.

---

## 2. Relationship to State Design

This document defines how the workflow moves.

`docs/architecture/state-design.md` defines what the workflow carries.

In short:

```text
graph-design.md
→ nodes, edges, routing, graph paths

state-design.md
→ state fields, ownership, errors, audit log, update rules
```

The graph should follow the state ownership rules defined in `state-design.md`.

---

## 3. Design Principles

### 3.1 One node, one responsibility

Each node should perform one clear workflow action.

Avoid nodes that classify, retrieve evidence, assess risk, and generate output all at once.

---

### 3.2 Nodes return partial state updates

Each node should update only the fields it owns.

This keeps graph execution easier to inspect and test.

---

### 3.3 Routing logic should be explicit

Conditional routing should be represented as a named route function.

Routing should be based on explicit state fields such as:

- `errors`
- `evidence_pack`
- `risk_assessment`

---

### 3.4 Graph should support both happy path and failure path

The graph should not only test successful execution.

It should also represent:

- missing required state;
- insufficient evidence;
- high-risk review route;
- structured error route.

---

### 3.5 Human review is currently represented as a placeholder

The current graph can route high-risk cases to a review placeholder.

It does not implement real interrupt/resume behavior yet.

---

### 3.6 Future tool calling should stay outside core triage nodes

Tool calling should not be embedded into classification, retrieval, or risk assessment nodes.

Future tool calling should be introduced after the EventRiskBrief and policy checks.

---

## 4. Graph Overview

Recommended graph structure:

```text
START
  ↓
normalize_signal
  ↓
classify_event
  ↓
deduplicate_event
  ↓
retrieve_evidence
  ↓
assess_risk
  ↓
route_after_risk_assessment
  ├── auto_brief → generate_event_risk_brief → END
  ├── human_review → human_review_placeholder → generate_event_risk_brief → END
  ├── request_more_evidence → request_more_evidence_placeholder → END
  └── error → error_handler → END
```

The main path is intentionally simple.

The goal is to validate:

- stateful node execution;
- conditional routing;
- basic evidence-backed risk assessment;
- graph path testing;
- future extension points.

---

## 5. Node Responsibilities

---

## 5.1 `normalize_signal_node`

### Purpose

Validate or normalize the incoming `RawSignal`.

### Reads

- `raw_signal`

### Writes

- `audit_log`
- `errors` if required input is missing or invalid

### Failure Behavior

If `raw_signal` is missing or invalid:

- append a structured error;
- route should eventually become `error`.

### Notes

If `RawSignal` is already validated by Pydantic before graph invocation, this node may be lightweight.

---

## 5.2 `classify_event_node`

### Purpose

Convert a `RawSignal` into an `EventCandidate`.

### Reads

- `raw_signal`

### Writes

- `event_candidate`
- `audit_log`
- `errors` if classification fails

### Failure Behavior

If classification fails:

- append a structured error;
- route should eventually become `error`.

### Notes

Current implementation can use rule-based classification.

LLM-based extraction is not required at this stage.

---

## 5.3 `deduplicate_event_node`

### Purpose

Convert one or more `EventCandidate` objects into an `EventCluster`.

### Reads

- `event_candidate`

### Writes

- `event_cluster`
- `audit_log`
- `errors` if required input is missing

### Current Behavior

A minimal single-candidate cluster is acceptable.

Complex deduplication is not required in the current graph.

### Future Behavior

Future versions may add:

- rule-based similarity;
- embedding similarity;
- LLM-based merge judgment;
- batch clustering.

---

## 5.4 `retrieve_evidence_node`

### Purpose

Retrieve context needed for risk assessment.

### Reads

- `event_cluster`
- dependency map
- playbooks
- historical cases

### Writes

- `evidence_pack`
- `audit_log`
- `errors` if evidence lookup fails

### Current Behavior

Use sample lookup or rule-based retrieval.

Full Agentic RAG is not required in the current graph.

### Important Distinction

Evidence lookup failure and weak evidence are different.

```text
lookup failure
→ error

lookup succeeds but evidence is weak
→ request_more_evidence
```

---

## 5.5 `assess_risk_node`

### Purpose

Assess risk using `event_cluster` and `evidence_pack`.

### Reads

- `event_cluster`
- `evidence_pack`

### Writes

- `risk_assessment`
- `audit_log`
- `errors` if risk assessment fails

### Failure Behavior

If required state is missing:

- append a structured error;
- route should become `error`.

### Notes

This node should not execute tool calls.

This node should not generate the final brief.

---

## 5.6 `route_after_risk_assessment`

### Purpose

Select the next graph path after risk assessment.

This is a conditional routing function, not a regular business node.

### Reads

- `errors`
- `evidence_pack`
- `risk_assessment`

### Returns

One of:

```text
auto_brief
human_review
request_more_evidence
error
```

### Routing Order

Recommended order:

```text
if errors exist:
    error

else if evidence_pack is missing or retrieval quality is too low:
    request_more_evidence

else if risk_assessment.requires_human_review is true:
    human_review

else:
    auto_brief
```

### Notes

The route function determines the selected graph path.

`RiskAssessment.requires_human_review` is a routing signal, not the route itself.

---

## 5.7 `human_review_placeholder_node`

### Purpose

Represent the review-required path without implementing real interrupt/resume behavior.

### Reads

- `risk_assessment`
- `event_cluster`
- `evidence_pack`

### Writes

- `route_decision = human_review`
- `audit_log`

### Does Not Write

- `human_review_decision`

### Behavior

This node should not approve, reject, or edit the decision.

It only records that the case requires human review.

The graph may still generate a pending-review `EventRiskBrief`.

---

## 5.8 `generate_event_risk_brief_node`

### Purpose

Generate the final structured `EventRiskBrief`.

### Reads

- `event_cluster`
- `evidence_pack`
- `risk_assessment`
- `human_review_decision` if available

### Writes

- `event_risk_brief`
- `audit_log`
- `errors` if required input is missing

### Behavior

For normal auto-brief path:

```text
review_status = not_required
```

For review placeholder path:

```text
review_status = pending
```

This node should not generate a normal brief for the error path.

---

## 5.9 `request_more_evidence_placeholder_node`

### Purpose

Represent the insufficient-evidence path.

### Reads

- `evidence_pack`
- `risk_assessment` if available

### Writes

- `route_decision = request_more_evidence`
- `audit_log`

### Behavior

The current graph should not generate a normal `EventRiskBrief` for this path.

The output should indicate that more evidence is needed.

---

## 5.10 `error_handler_node`

### Purpose

Represent the structured error path.

### Reads

- `errors`

### Writes

- `route_decision = error`
- `audit_log`

### Behavior

This node should not generate a normal `EventRiskBrief`.

The workflow output should preserve structured errors for debugging and tests.

---

## 6. Edge Design

### 6.1 Fixed Edges

Fixed edges define the main workflow order:

```text
START
→ normalize_signal
→ classify_event
→ deduplicate_event
→ retrieve_evidence
→ assess_risk
```

These steps are sequential because each step depends on the output of the previous step.

---

### 6.2 Conditional Edge

After `assess_risk`, the graph uses conditional routing:

```text
assess_risk
→ route_after_risk_assessment
```

Possible destinations:

```text
auto_brief
human_review
request_more_evidence
error
```

---

### 6.3 Destination Edges

Recommended destination edges:

```text
auto_brief
→ generate_event_risk_brief
→ END
```

```text
human_review
→ human_review_placeholder
→ generate_event_risk_brief
→ END
```

```text
request_more_evidence
→ request_more_evidence_placeholder
→ END
```

```text
error
→ error_handler
→ END
```

---

## 7. Conditional Routing

The routing function should be deterministic and testable.

Suggested logic:

```python
def route_after_risk_assessment(state: EventFlowState) -> str:
    if state.get("errors"):
        return "error"

    evidence_pack = state.get("evidence_pack")
    if evidence_pack is None:
        return "request_more_evidence"

    if evidence_pack.retrieval_quality < MIN_RETRIEVAL_QUALITY:
        return "request_more_evidence"

    risk_assessment = state.get("risk_assessment")
    if risk_assessment is None:
        return "error"

    if risk_assessment.requires_human_review:
        return "human_review"

    return "auto_brief"
```

`MIN_RETRIEVAL_QUALITY` should be configurable.

The route function should not rely on unstructured natural language.

---

## 8. Error Handling Path

The error path handles workflow execution problems.

Examples:

- missing `raw_signal`;
- missing `event_candidate`;
- failed classification;
- failed evidence lookup;
- missing `risk_assessment`;
- brief generation precondition failure.

The error path should produce:

```text
route_decision = error
errors populated
audit_log updated
event_risk_brief absent
```

The error path should not produce a normal `EventRiskBrief`.

---

## 9. Human Review Placeholder

The current graph supports a review-required route without implementing real Human-in-the-loop execution.

The placeholder should:

- set `route_decision = human_review`;
- append an audit entry;
- allow a pending-review brief to be generated;
- avoid creating a fake `HumanReviewDecision`.

Expected pending-review brief behavior:

```text
review_status = pending
```

Future real Human-in-the-loop behavior may add:

- interrupt/resume;
- checkpointer;
- thread ID;
- review payload;
- reviewer decision handling;
- approval/edit/reject paths.

---

## 10. Test Strategy

The graph should be tested by graph path, not only by individual nodes.

---

## 10.1 Low-risk Auto Brief Path

Input:

```text
low-risk product_release
```

Expected:

```text
route_decision = auto_brief
event_risk_brief exists
review_status = not_required
errors empty
```

---

## 10.2 High-risk Review Placeholder Path

Input:

```text
high-risk security_advisory
or service_incident affecting critical dependency
```

Expected:

```text
route_decision = human_review
event_risk_brief exists
review_status = pending
human_review_decision absent
errors empty
```

---

## 10.3 Request More Evidence Path

Input:

```text
unknown vendor
or evidence retrieval quality below threshold
```

Expected:

```text
route_decision = request_more_evidence
event_risk_brief absent
errors empty or warning-only
audit_log includes evidence insufficiency
```

---

## 10.4 Error Path

Input:

```text
missing raw_signal
or malformed state
```

Expected:

```text
route_decision = error
errors not empty
event_risk_brief absent
audit_log includes error entry
```

---

## 10.5 Audit Log Path Check

For successful runs, tests may verify that `audit_log` includes entries from expected nodes:

```text
normalize_signal
classify_event
deduplicate_event
retrieve_evidence
assess_risk
generate_event_risk_brief
```

This helps verify that the graph followed the intended path.

---

## 11. Current Scope and Future Extensions

### Current Scope

The current graph supports:

- stateful event triage workflow;
- rule-based or sample lookup logic;
- minimal deduplication;
- evidence pack generation;
- risk assessment;
- conditional routing;
- human review placeholder;
- structured error path;
- graph path tests.

### Future Extensions

Future versions may add:

- real Human-in-the-loop interrupt/resume;
- checkpoint persistence;
- Agentic RAG;
- query rewriting;
- retrieval quality evaluator;
- action recommendation;
- controlled tool calling;
- replay evaluation;
- richer observability and tracing.

These should be added only when the roadmap calls for them.
