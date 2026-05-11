# Sample Data

This folder contains synthetic sample data for EventFlow Agent.

The data is used for schema validation, baseline workflow development, LangGraph workflow testing, evidence retrieval, and replay evaluation.

---

## 1. Purpose

The sample dataset supports M1 and later milestones.

It provides:

- raw external signals;
- a simulated SaaS dependency map;
- response playbooks;
- synthetic historical cases;
- labeled evaluation cases.

The dataset should be realistic enough to support event triage scenarios, but it must remain clearly synthetic and safe to publish.

---

## 2. Synthetic Data Policy

All sample events in this repository are synthetic.

Public vendor and dependency names may be used to make the dataset realistic, but the event contents must not represent actual incidents.

Rules:

- Do not use real incident IDs.
- Do not use real CVE IDs.
- Do not use real status page URLs.
- Do not use real customer data.
- Do not use private company data.
- Set `is_synthetic: true` for all M1 sample records that represent events or historical cases.
- Use null or `example.com`-style placeholder URLs for synthetic records.

Acceptable:

```text
GitHub Actions is used as a public dependency name.
A synthetic event describes delayed workflow job starts.
The source URL is null or https://example.com/simulated/github-actions-incident-001.
```

Not acceptable:

```text
A real GitHub incident ID.
A real status page URL for a specific outage.
A real CVE ID.
A claim that the synthetic event actually occurred.
```

---

## 3. Vendor and Dependency Naming Policy

M1 may use public vendor or dependency names to simulate realistic SaaS dependencies.

Recommended dependency names:

```text
GitHub Actions
Stripe API
OpenAI API
AWS S3
Vercel
PostgreSQL
FastAPI
Pydantic
LangGraph
SendGrid
```

These names are used only to simulate dependency relationships.

The dataset must not claim that synthetic events actually happened to these vendors.

---

## 4. Files

Expected data layout:

```text
data/
  README.md
  samples/
    raw_signals.jsonl
    dependency_map.json
    playbooks.jsonl
    historical_cases.jsonl
  eval/
    eval_cases.jsonl
```

---

## 5. File Formats

---

## 5.1 `samples/raw_signals.jsonl`

One `RawSignal` record per line.

Purpose:

- simulate public external signals;
- provide input for schema validation;
- provide input for baseline workflow;
- provide input for LangGraph workflow later.

Each record should include:

```text
signal_id
source_type
vendor
title
content
published_at
source_url
metadata
is_synthetic
```

M1 target size:

```text
20-30 records
```

Recommended event distribution:

```text
service_incident: 6-8
security_advisory: 5-7
api_change: 5-7
product_release: 5-7
```

---

## 5.2 `samples/dependency_map.json`

Defines the simulated SaaS product and its external dependencies.

Purpose:

- support dependency impact analysis;
- make risk assessment explainable;
- connect raw signals to internal product modules.

Suggested structure:

```text
product_name
modules[]
```

Each module should include:

```text
module_id
module_name
business_criticality
dependencies[]
```

Each dependency should include:

```text
dependency_id
vendor
dependency_name
dependency_type
criticality
used_for
```

Example simulated modules:

```text
CI/CD Pipeline -> GitHub Actions
Billing -> Stripe API
AI Assistant -> OpenAI API
Object Storage -> AWS S3
Web Hosting -> Vercel
Database -> PostgreSQL
Backend API -> FastAPI / Pydantic
Agent Workflow -> LangGraph
Customer Email -> SendGrid
```

---

## 5.3 `samples/playbooks.jsonl`

One playbook record per line.

Purpose:

- define response guidance;
- connect event type and dependency criticality to risk level;
- support recommended actions.

Each record should include:

```text
playbook_id
event_type
dependency_criticality
risk_level
recommended_action
review_required
guidance
```

Recommended actions for MVP:

```text
ignore
watch
notify_support
create_internal_issue
escalate_to_engineering
request_more_evidence
```

Do not include remediation actions such as:

```text
auto_fix
rollback
deploy_hotfix
patch_dependency
restart_service
```

---

## 5.4 `samples/historical_cases.jsonl`

One historical case per line.

Purpose:

- provide synthetic past cases for future retrieval;
- support evidence-backed risk assessment;
- support replay evaluation later.

Each record should include:

```text
case_id
event_type
vendor
affected_dependencies
summary
risk_level
action_taken
outcome
lessons_learned
is_synthetic
```

All M1 historical cases must be synthetic.

---

## 5.5 `eval/eval_cases.jsonl`

One eval case per line.

Purpose:

- support replay evaluation;
- define expected classification, risk level, route, and recommended action;
- compare workflow versions later.

Each record should include:

```text
eval_id
input_signal_id
expected_event_type
expected_affected_dependencies
expected_risk_level
expected_route
expected_recommended_action
label_rationale
label_status
```

Allowed `label_status` values:

```text
draft
reviewed
```

AI may help draft eval labels, but labels should be manually reviewed before being treated as ground truth.

---

## 6. Recommended Risk Distribution

For 20-30 raw signals, use a balanced distribution:

```text
low: 5-7
medium: 6-8
high: 6-8
critical: 1-3
```

Avoid making every event high risk.

The dataset should include:

- clearly irrelevant or low-risk events;
- medium-risk operational events;
- high-risk security or core dependency events;
- a small number of critical events;
- repeated or related signals for future deduplication tests.

---

## 7. Maintenance Rules

When adding or editing sample data:

1. Keep all records internally consistent.
2. Every raw signal should reference a known vendor/dependency unless intentionally irrelevant.
3. High-risk labels must be explainable by dependency criticality, playbook guidance, or evidence.
4. Eval labels should not be accepted blindly from AI output.
5. Do not introduce new event types without updating `docs/architecture/data-model.md`.
6. Do not introduce new recommended actions without updating `docs/architecture/data-model.md`.
7. Do not create too many vendors too early.
8. Keep synthetic events realistic but clearly non-real.
9. Do not use real incident IDs, real CVE IDs, or real status page URLs.
10. Preserve stable IDs once eval cases reference them.

---

## 8. Validation

M1 validation should check:

- JSON and JSONL files are parseable.
- Required fields are present.
- Enum values are valid.
- `confidence` fields are between 0 and 1 where applicable.
- `is_synthetic` is true for synthetic records.
- eval cases reference existing raw signals.
- playbooks use allowed event types and actions.
- high-risk eval labels have a clear rationale.

Validation should be implemented with tests under:

```text
tests/unit/
tests/eval/
```

---

## 9. Data Review Checklist

Before accepting generated sample data, check:

- [ ] Is every event clearly synthetic?
- [ ] Are public vendor names used only as dependency names?
- [ ] Are real incident IDs avoided?
- [ ] Are real CVE IDs avoided?
- [ ] Are real status page URLs avoided?
- [ ] Does each event map to dependency context or intentionally not map?
- [ ] Are risk labels explainable?
- [ ] Are recommended actions from the allowed action set?
- [ ] Are eval labels reviewed or marked as draft?
- [ ] Is the event distribution balanced?
- [ ] Are there some duplicate or related signals for future deduplication tests?
