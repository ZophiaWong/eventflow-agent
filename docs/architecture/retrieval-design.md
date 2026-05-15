# Retrieval Design

This document defines the evidence retrieval design for EventFlow Agent.

The goal of this document is to specify how EventFlow retrieves dependency context, playbooks, historical cases, and source evidence to support risk assessment.

This is an architecture contract for M4. Implementation should follow this design unless the roadmap or architecture docs are updated.

---

## 1. Purpose

Evidence retrieval in EventFlow Agent is not generic knowledge-base Q&A.

It is used to support external SaaS event triage.

Given an `EventCluster`, the retrieval layer should answer:

- Does this event affect a known dependency?
- Which product module may be impacted?
- How critical is that dependency?
- Is there a matching playbook?
- Are there similar historical cases?
- Is the available evidence strong enough to support risk assessment?

The output of retrieval is an `EvidencePack`.

`EvidencePack` becomes the boundary between retrieval and risk assessment.

```text
EventCluster
→ RetrievalQuery
→ Evidence Retrieval
→ EvidencePack
→ Evidence Evaluation
→ RiskAssessment or request_more_evidence
```

The retrieval layer should make risk assessment more grounded, testable, and explainable.

---

## 2. Current Scope

The current retrieval design focuses on structured, deterministic retrieval over local sample data.

In scope:

- structured `RetrievalQuery`;
- dependency map retrieval;
- playbook retrieval;
- historical case retrieval;
- source evidence support;
- `EvidencePack` construction;
- rule-based retrieval quality scoring;
- conditional routing based on evidence quality;
- optional single retry with rule-based query expansion.

Out of scope:

- production vector database;
- real web crawling;
- real-time indexing;
- complex chunking pipeline;
- LLM-based retrieval judge;
- multi-round autonomous search;
- production semantic search;
- side-effecting tool calls.

---

## 3. Relationship to Existing Architecture

This document complements existing architecture documents.

```text
docs/architecture/data-model.md
→ defines EvidencePack, Playbook, HistoricalCase, DependencyMap, and related models

docs/architecture/state-design.md
→ defines evidence_pack, route_decision, errors, and audit_log in workflow state

docs/architecture/graph-design.md
→ defines retrieve_evidence, evaluate_evidence, and conditional routing

docs/architecture/retrieval-design.md
→ defines how evidence is retrieved, evaluated, and routed
```

This document should not redefine the full workflow state or graph structure. It should only define retrieval-specific behavior.

---

## 4. Retrieval Sources

M4 retrieval uses local sample data.

---

## 4.1 Dependency Map

The dependency map answers:

```text
Does this external event affect a dependency used by the simulated SaaS product?
```

It should provide:

- dependency ID;
- vendor name;
- dependency name;
- dependency type;
- product module;
- business criticality;
- usage description.

Example:

```text
GitHub Actions
→ CI/CD Pipeline
→ high criticality
→ used for deployment and automated tests
```

The dependency map is the most important retrieval source.

If no dependency can be matched, EventFlow usually should not proceed to confident risk assessment.

---

## 4.2 Playbooks

Playbooks answer:

```text
How should the team respond to this type of event for a dependency with this criticality?
```

A playbook should explain:

- event type;
- dependency criticality;
- suggested risk level;
- recommended action;
- whether review is required;
- response guidance.

Example:

```text
service_incident + high criticality
→ risk_level = high
→ recommended_action = notify_support
→ review_required = true
```

Playbooks connect evidence retrieval to action recommendation.

---

## 4.3 Historical Cases

Historical cases answer:

```text
Have we seen similar synthetic events before, and what happened?
```

A historical case should contain:

- event type;
- vendor;
- affected dependencies;
- summary;
- risk level;
- action taken;
- outcome;
- lessons learned.

Historical cases are useful for context, but they are not mandatory for every event.

A new event can still have sufficient evidence without a similar historical case if dependency and playbook evidence are strong.

---

## 4.4 Source Evidence

Source evidence refers to the current raw signal or source references associated with the event.

For synthetic M1/M4 data, source evidence may be represented by:

- `source_signal_ids`;
- `source_type`;
- synthetic title and content;
- placeholder or null source URL;
- `is_synthetic = true`.

M4 does not implement a full citation system.

However, the workflow should preserve source references so that risk assessment and Event Risk Brief generation do not rely on unsupported claims.

---

## 5. Retrieval Query Design

M4 should use structured retrieval queries.

A structured query is preferred over a free-form natural language query because it is:

- easier to test;
- easier to debug;
- compatible with sample data;
- independent of LLM behavior;
- easier to upgrade later.

---

## 5.1 RetrievalQuery

`RetrievalQuery` should be built from `EventCluster`.

Suggested fields:

```text
query_id
event_type
vendor
affected_dependencies
keywords
summary
attempt
```

Example:

```json
{
  "query_id": "rq_001",
  "event_type": "service_incident",
  "vendor": "GitHub Actions",
  "affected_dependencies": ["GitHub Actions"],
  "keywords": ["workflow", "job", "delay", "ci/cd"],
  "summary": "Workflow job start delays affecting CI/CD pipeline.",
  "attempt": 0
}
```

---

## 5.2 Query Construction

The query builder should extract:

- event type from `EventCluster`;
- vendor from `EventCluster`;
- affected dependencies from `EventCluster`;
- keywords from title, summary, vendor, dependency, and module names.

The query builder should not call an LLM in M4.

---

## 5.3 Query Expansion

Query expansion is optional in M4.

If implemented, it should be rule-based.

Examples:

```text
GitHub Actions
→ GitHub CI
→ workflow jobs
→ CI/CD pipeline
```

```text
Stripe API
→ billing
→ payment processing
→ checkout
```

```text
OpenAI API
→ AI assistant
→ model API
→ LLM provider
```

Query expansion should only be used after weak evidence is detected.

---

## 6. Retriever Responsibilities

Retrieval should be decomposed into small retrievers.

---

## 6.1 DependencyRetriever

### Purpose

Find dependencies in `dependency_map.json` that match the event.

### Input

```text
RetrievalQuery
DependencyMap
```

### Output

```text
matched_dependencies
dependency_match_score
```

### Matching Signals

- exact dependency name match;
- vendor alias match;
- module name match;
- dependency keyword match.

### Notes

Dependency retrieval should be deterministic in M4.

---

## 6.2 PlaybookRetriever

### Purpose

Find playbooks that match event type and dependency criticality.

### Input

```text
RetrievalQuery
matched_dependencies
playbooks
```

### Output

```text
matched_playbooks
playbook_match_score
```

### Matching Signals

- event type;
- dependency criticality;
- recommended risk level;
- review requirement.

### Notes

Playbook retrieval should explain recommended actions.

---

## 6.3 HistoricalCaseRetriever

### Purpose

Find synthetic historical cases similar to the current event.

### Input

```text
RetrievalQuery
historical_cases
```

### Output

```text
matched_historical_cases
historical_case_score
```

### Matching Signals

- same vendor;
- same event type;
- overlapping dependency;
- similar module or keyword;
- similar action or outcome.

### Notes

Historical case retrieval is useful but not required for every event.

---

## 6.4 EvidenceBuilder

### Purpose

Combine dependency, playbook, historical case, and source evidence into an `EvidencePack`.

### Input

```text
RetrievalQuery
dependency retrieval result
playbook retrieval result
historical case retrieval result
source refs
```

### Output

```text
EvidencePack
```

### Notes

EvidenceBuilder should not perform risk assessment.

It only builds the evidence boundary object.

---

## 6.5 EvidenceEvaluator

### Purpose

Evaluate whether the `EvidencePack` is strong enough to support risk assessment.

### Input

```text
EvidencePack
```

### Output

```text
retrieval_quality
missing_evidence_reasons
evidence_sufficiency
```

### Notes

EvidenceEvaluator should use rule-based scoring in M4.

It should not use an LLM judge as the primary routing mechanism.

---

## 7. EvidencePack Design

`EvidencePack` is the boundary between retrieval and risk assessment.

It should contain enough information for downstream risk assessment without requiring the risk node to perform retrieval again.

Suggested fields:

```text
evidence_id
query
source_signal_ids
matched_dependencies
matched_playbooks
matched_historical_cases
evidence_notes
missing_evidence_reasons
retrieval_quality
attempt_count
```

---

## 7.1 Design Rules

### Retrieval should not do risk assessment

Retrieval returns evidence.

Risk assessment decides risk.

---

### Risk assessment should not perform retrieval

Risk assessment should consume `EvidencePack`.

This keeps retrieval and judgment separate.

---

### Evidence should preserve references

Evidence should include IDs or references to:

- raw signals;
- dependencies;
- playbooks;
- historical cases.

This supports debugging, replay evaluation, and Event Risk Brief generation.

---

## 8. Retrieval Quality Evaluation

M4 should use rule-based retrieval quality scoring.

The purpose is to make evidence sufficiency:

- deterministic;
- explainable;
- testable;
- independent of LLM judgment.

---

## 8.1 Composite Score

Recommended formula:

```text
retrieval_quality =
  dependency_match_score * 0.4
+ playbook_match_score * 0.3
+ historical_case_score * 0.2
+ source_support_score * 0.1
```

Weight rationale:

- `dependency_match_score` is most important because EventFlow must know whether the event affects the simulated SaaS product.
- `playbook_match_score` explains the recommended action and review policy.
- `historical_case_score` adds useful context but should not be mandatory.
- `source_support_score` prevents unsupported risk claims.

---

## 8.2 Dependency Match Score

Purpose:

```text
Measure whether the event maps to a known dependency.
```

Suggested scoring:

| Score | Meaning                                          |
| ----: | ------------------------------------------------ |
| `1.0` | Exact dependency match                           |
| `0.8` | Vendor alias or normalized dependency name match |
| `0.6` | Module-level match                               |
| `0.3` | Weak keyword match                               |
| `0.0` | No match                                         |

Examples:

```text
Raw signal vendor: GitHub Actions
Dependency map contains: GitHub Actions
→ 1.0
```

```text
Raw signal mentions: workflow jobs
Dependency aliases contain: GitHub CI, workflow jobs
→ 0.8
```

```text
Raw signal mentions: CI pipeline delays
Dependency map module: CI/CD Pipeline
→ 0.6
```

```text
Unknown vendor, no module or keyword match
→ 0.0
```

For multiple dependencies, M4 may use the maximum score.

---

## 8.3 Playbook Match Score

Purpose:

```text
Measure whether the system found a playbook that explains risk and recommended action.
```

Suggested scoring:

| Score | Meaning                                          |
| ----: | ------------------------------------------------ |
| `1.0` | Exact match: event type + dependency criticality |
| `0.8` | Event type match + adjacent criticality          |
| `0.6` | Event type match only                            |
| `0.4` | Dependency criticality match only                |
| `0.0` | No relevant playbook                             |

Examples:

```text
event_type = service_incident
dependency_criticality = high
playbook exists for service_incident + high
→ 1.0
```

```text
event_type = api_change
generic api_change playbook exists
→ 0.6
```

---

## 8.4 Historical Case Score

Purpose:

```text
Measure whether similar synthetic historical cases were found.
```

Suggested scoring:

| Score | Meaning                                                |
| ----: | ------------------------------------------------------ |
| `1.0` | Same vendor + same event type + overlapping dependency |
| `0.8` | Same event type + overlapping dependency               |
| `0.6` | Same vendor + similar event type                       |
| `0.4` | Same event type only                                   |
| `0.0` | No relevant historical case                            |

Examples:

```text
Current event: GitHub Actions service_incident
Historical case: GitHub Actions service_incident affecting CI/CD
→ 1.0
```

```text
Current event: Pydantic security_advisory
Historical case: FastAPI security_advisory
→ 0.4 or 0.6 depending on matching rules
```

Historical case score is useful but should not dominate retrieval quality.

---

## 8.5 Source Support Score

Purpose:

```text
Measure whether the current signal has enough source content to support retrieval.
```

Suggested scoring:

| Score | Meaning                                                           |
| ----: | ----------------------------------------------------------------- |
| `1.0` | Title + content + source_type + synthetic marker/source ref exist |
| `0.7` | Title + content exist, source URL is null because synthetic       |
| `0.5` | Title exists but content is weak                                  |
| `0.0` | Missing meaningful source content                                 |

For synthetic sample data, a complete synthetic signal can receive full source support.

Example:

```text
title + content + source_type + is_synthetic = true
→ 1.0
```

---

## 8.6 Sufficiency Thresholds

Recommended thresholds:

```text
retrieval_quality >= 0.70
→ sufficient

0.45 <= retrieval_quality < 0.70
→ weak, retry if attempts remain

retrieval_quality < 0.45
→ insufficient
```

Hard gate:

```text
if dependency_match_score == 0:
    evidence_sufficiency = insufficient
```

Reason:

EventFlow is primarily about determining whether external events affect the simulated SaaS product.

If the event cannot be mapped to a dependency, the workflow should not proceed to confident risk assessment.

---

## 9. Agentic Retrieval Loop

M4 can represent Agentic RAG as a small dynamic retrieval loop.

The goal is not unlimited autonomous search.

The goal is:

```text
retrieve
→ evaluate
→ decide whether to proceed, retry, or request more evidence
```

---

## 9.1 Minimal Loop

Recommended minimal loop:

```text
retrieve_evidence
→ evaluate_evidence
→ route_after_evidence
    ├── sufficient → assess_risk
    └── insufficient → request_more_evidence
```

---

## 9.2 Optional Retry Loop

Optional stronger version:

```text
retrieve_evidence
→ evaluate_evidence
→ route_after_evidence
    ├── sufficient → assess_risk
    ├── retry → rewrite_retrieval_query → retrieve_evidence
    └── insufficient → request_more_evidence
```

M4 should use at most one retry.

---

## 9.3 Why At Most One Retry?

One retry is enough to handle common query weakness:

- vendor alias mismatch;
- missing dependency keyword;
- module keyword not included;
- event summary too narrow.

More retries increase:

- workflow complexity;
- latency;
- test instability;
- unclear failure diagnosis.

If retrieval is still weak after one retry, the problem is likely missing data rather than query wording.

The correct route is then:

```text
request_more_evidence
```

---

## 9.4 Query Rewrite Behavior

If implemented, query rewrite should be rule-based in M4.

Examples:

```text
vendor alias expansion
dependency keyword expansion
module keyword expansion
event type synonym expansion
```

LLM-based rewrite is a future extension.

---

## 9.5 Retry Failure Behavior

If retry still produces weak evidence:

```text
route_decision = request_more_evidence
retrieval_attempts = max_retrieval_attempts
missing_evidence_reasons populated
event_risk_brief should not be generated as a normal brief
audit_log should record insufficient evidence
```

Example missing evidence reasons:

```json
[
  "No dependency matched vendor 'Unknown Vendor'.",
  "No playbook matched event_type 'api_change' with dependency criticality.",
  "No relevant historical case found."
]
```

---

## 10. Graph Integration

M3 graph segment:

```text
retrieve_evidence
→ assess_risk
```

M4 graph segment:

```text
retrieve_evidence
→ evaluate_evidence
→ route_after_evidence
    ├── sufficient → assess_risk
    ├── retry → rewrite_retrieval_query → retrieve_evidence
    └── insufficient → request_more_evidence
```

If retry is not implemented yet, the graph may use:

```text
retrieve_evidence
→ evaluate_evidence
→ route_after_evidence
    ├── sufficient → assess_risk
    └── insufficient → request_more_evidence
```

---

## 11. Routing Rules

Recommended routing order:

```text
if retrieval failed due to system error:
    error

else if evidence is sufficient:
    assess_risk

else if evidence is weak and retry_count < max_retrieval_attempts:
    retry_retrieval

else:
    request_more_evidence
```

Important distinction:

```text
retrieval failure
→ error

weak or insufficient evidence
→ retry or request_more_evidence
```

Retrieval failure examples:

- invalid data file;
- malformed dependency map;
- retriever exception;
- missing required input state.

Weak evidence examples:

- no dependency match;
- no playbook match;
- no historical case;
- low retrieval quality score;
- missing source support.

---

## 12. Vector Database Future Extension

Vector database integration is not part of M4.

If added later, it should be introduced carefully.

---

## 12.1 Main Difficulties

Vector retrieval introduces several new design problems:

- how to chunk dependency, playbook, and historical case data;
- how to combine metadata filtering with semantic search;
- how to evaluate top-k retrieval quality;
- how to avoid semantically similar but business-irrelevant results;
- how to keep tests deterministic;
- how to manage embedding model, index refresh, and thresholds.

---

## 12.2 Recommended Upgrade Path

If vector retrieval is added later:

```text
Step 1: Keep structured retrieval as baseline.
Step 2: Add vector retrieval only for historical cases first.
Step 3: Keep dependency map and playbooks as structured lookup.
Step 4: Compare structured historical retrieval vs vector historical retrieval.
Step 5: Evaluate with retrieval_eval_cases.
```

Do not vectorize everything at once.

---

## 13. LLM Judge Future Extension

LLM-based retrieval judgment is not part of M4.

Rule-based scoring should remain the primary workflow routing mechanism in M4.

---

## 13.1 Main Difficulties

LLM judge introduces:

- unstable scores;
- unclear rubric boundaries;
- additional cost;
- additional latency;
- harder test assertions;
- risk of hiding dataset quality issues.

---

## 13.2 Recommended Upgrade Path

If LLM judge is added later:

```text
Step 1: Keep rule-based retrieval_quality as primary route control.
Step 2: Use LLM judge only for offline evaluation.
Step 3: Compare rule score with LLM score.
Step 4: Investigate conflict cases manually.
Step 5: Calibrate rubric before using it in workflow.
```

LLM judge should not directly control production-like routing until its behavior is evaluated.

---

## 14. Test Strategy

M4 should include unit tests and graph path tests.

---

## 14.1 Dependency Retrieval Tests

Example:

```text
Input: GitHub Actions service incident
Expected: retrieves CI/CD Pipeline dependency
```

---

## 14.2 Playbook Retrieval Tests

Example:

```text
Input: service_incident + high criticality dependency
Expected: retrieves matching service incident high-criticality playbook
```

---

## 14.3 Historical Case Retrieval Tests

Example:

```text
Input: Pydantic security advisory
Expected: retrieves similar historical security case if available
```

---

## 14.4 Evidence Quality Tests

Examples:

```text
dependency + playbook + historical case present
→ retrieval_quality high
```

```text
unknown vendor
→ retrieval_quality low
```

```text
dependency_match_score == 0
→ evidence_sufficiency insufficient
```

---

## 14.5 Graph Route Tests

Examples:

```text
sufficient evidence
→ assess_risk
```

```text
insufficient evidence
→ request_more_evidence
```

```text
retrieval failure
→ error
```

---

## 14.6 Retry Tests

If retry is implemented:

```text
first retrieval weak
→ query expansion
→ second retrieval sufficient
→ assess_risk
```

```text
first retrieval weak
→ query expansion
→ second retrieval still weak
→ request_more_evidence
```

---

## 15. Implementation Modules

Recommended module layout:

```text
src/eventflow/retrieval/
  __init__.py
  query_builder.py
  dependency_retriever.py
  playbook_retriever.py
  historical_case_retriever.py
  evidence_builder.py
  evidence_evaluator.py
```

Recommended node layout:

```text
src/eventflow/nodes/retrieve_evidence.py
src/eventflow/nodes/evaluate_evidence.py
src/eventflow/nodes/rewrite_retrieval_query.py  # optional
```

Recommended tests:

```text
tests/unit/retrieval/
  test_dependency_retriever.py
  test_playbook_retriever.py
  test_historical_case_retriever.py
  test_evidence_evaluator.py

tests/integration/
  test_m4_retrieval_graph_paths.py

tests/eval/
  test_retrieval_eval_cases.py
```

---

## 16. Non-goals

M4 explicitly does not include:

- production vector database;
- real web crawling;
- real-time indexing;
- complex chunking pipeline;
- LLM-based retrieval judge;
- autonomous external search;
- side-effecting tool calls;
- complete risk engine rewrite;
- production observability platform.

---

## 17. Future Extensions

Future versions may add:

- semantic retrieval;
- pgvector or Chroma;
- LLM-based query rewriting;
- reranking;
- retrieval eval pipeline;
- LangSmith trace integration;
- online retrieval monitoring;
- source reliability scoring;
- richer citation support.

These are future extensions, not M4 requirements.
