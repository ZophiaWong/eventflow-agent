# M2 Rule-Based Baseline

## Purpose

M2 adds a deterministic baseline workflow before LangGraph, LLM extraction, RAG, or tool calling.

The baseline processes one validated `RawSignal` at a time and produces either:

- an `EventRiskBrief`; or
- a structured baseline error when evidence is missing or the event cannot be classified.

This gives later milestones a clear reference behavior and makes each workflow stage independently testable.

## Pipeline

```text
RawSignal
-> normalize_signal
-> classify_rule_based
-> retrieve_playbook_rule_based
-> assess_risk_rule_based
-> generate_brief
```

## Node Responsibilities

- `normalize_signal` preserves the validated `RawSignal` contract for M2 sample data.
- `classify_rule_based` uses source type and keyword rules to produce an `EventCandidate`.
- `retrieve_playbook_rule_based` matches dependency-map entries and selects a playbook by event type and dependency criticality.
- `assess_risk_rule_based` uses the matched playbook and evidence quality to produce a `RiskAssessment`.
- `generate_brief` converts baseline artifacts into an `EventRiskBrief`.

## CLI Usage

Run one sample signal:

```bash
python -m eventflow.baseline --signal-id sig_001 --data-dir data --pretty
```

Run all sample signals:

```bash
python -m eventflow.baseline --all --data-dir data --pretty
```

Run draft eval smoke metrics:

```bash
python -m eventflow.baseline --eval --data-dir data --pretty
```

## Known Limits

- The baseline processes one signal at a time.
- Deduplication and `EventCluster` behavior are deferred.
- Historical cases are not retrieved yet.
- Eval labels are draft labels, so metrics are smoke checks rather than ground truth.
- No external APIs, LLM calls, side-effecting tools, or human review interrupts are used.

## Interview Takeaway

M2 demonstrates that the project has deterministic, testable behavior before adding agentic orchestration. The baseline makes later LangGraph and LLM work easier to evaluate because there is already a structured reference path from raw signal to risk brief.
