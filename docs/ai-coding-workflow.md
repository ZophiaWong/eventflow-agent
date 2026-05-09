# AI Coding Workflow

This document defines how Codex should be used in EventFlow Agent.

The goal is to increase development speed without losing architectural control, testability, or interview understanding.

---

## 1. Core Principle

Codex can assist implementation, but it should not own the architecture.

The human developer owns:

- project scope;
- architecture decisions;
- data model decisions;
- safety boundaries;
- final code review;
- interview explanation.

Codex helps with:

- implementation;
- test generation;
- scoped refactoring;
- documentation drafts;
- code review;
- failure analysis.

---

## 2. Default Workflow

For non-trivial tasks, use:

```text
Explore
→ Plan
→ Implement
→ Verify
→ Review
→ Summarize
```

For large features, expand this into:

```text
Feature Slice
→ Architecture Contract
→ Implementation Plan
→ Code
→ Verification
→ Code Review
→ Interview Extraction
```

---

## 3. Explore

Before coding, inspect relevant files.

Always inspect:

- current user request;
- `docs/project-roadmap.md`;
- relevant architecture docs;
- relevant source files;
- relevant tests.

Do not start coding immediately if the task:

- touches more than one module;
- changes schemas;
- changes LangGraph workflow behavior;
- changes routing logic;
- adds dependencies;
- adds LLM calls;
- adds tool calling;
- changes evaluation behavior.

---

## 4. Plan

For non-trivial tasks, provide a short implementation plan before editing files.

The plan should include:

```text
Goal
Assumptions
Files to inspect
Files to modify
Out of scope
Implementation steps
Tests to add or update
Verification commands
```

Keep the plan concise.

Do not write implementation code during planning unless explicitly requested.

---

## 5. Feature Slice

Use this step when the request is vague or large.

Purpose:

- reduce vague ideas into a small, testable feature;
- define scope clearly;
- prevent uncontrolled changes;
- preserve interview explainability.

Feature slice format:

```text
Feature name
Goal
Smallest useful slice
In scope
Out of scope
Files to inspect
Files allowed to modify
Acceptance criteria
Tests required
Interview takeaway
```

Example:

```text
Feature: RawSignal schema validation

In scope:
- Define RawSignal Pydantic model
- Validate sample raw_signals.jsonl
- Add unit tests

Out of scope:
- LLM extraction
- LangGraph workflow
- external API ingestion
```

---

## 6. Architecture Contract

Use this step for schemas, LangGraph nodes, routing, retrieval, human review, or tool calling.

Architecture contract format:

```text
Module or node name
Responsibility
Input schema
Output schema
State fields read
State fields written
Routing behavior
Error behavior
Audit log behavior
Tests required
```

Example:

```text
Node: assess_risk_node

Reads:
- event_candidate
- evidence_pack

Writes:
- risk_assessment
- route_decision
- audit_log

Routes:
- high or critical risk -> human_review
- low or medium risk -> generate_brief
```

---

## 7. Implement

Implementation rules:

- keep diffs small;
- do not change unrelated files;
- follow existing schemas;
- add tests with behavior changes;
- prefer deterministic logic before LLM calls;
- avoid new dependencies unless justified;
- do not implement post-MVP items early;
- do not hide side effects inside workflow nodes.

If the task requires a dependency change, explain:

```text
Dependency name
Why it is needed
Alternatives considered
Current milestone relevance
```

---

## 8. Verify

After implementation, verify the change.

Use relevant commands:

```bash
python -m pytest
python -m pytest tests/unit
python -m pytest tests/integration
python -m ruff check .
python -m mypy src
```

If a command cannot be run, state why.

Do not say tests passed unless they actually ran.

Verification summary should include:

```text
Commands run
Results
Commands not run
Reason not run
Known gaps
```

---

## 9. Review

Before accepting a non-trivial change, review against:

```text
docs/code-review-checklist.md
```

Focus on:

- scope control;
- schema safety;
- LangGraph state safety;
- routing correctness;
- evidence-backed risk logic;
- Human-in-the-loop and tool safety;
- tests;
- documentation;
- dependencies;
- security;
- interview explainability.

---

## 10. Summarize

For coding tasks, final response should include:

```text
Summary:
- ...

Files changed:
- ...

Validation:
- ...

Known gaps:
- ...

Next step:
- ...
```

For planning tasks, final response should include:

```text
Goal:
...

Assumptions:
...

Plan:
...

Out of scope:
...

Open questions:
...
```

Do not overstate completion.

Do not claim implementation details that do not exist.

---

## 11. Interview Extraction

After a feature is completed and tested, optionally create a short feature note under:

```text
docs/project-notes/feature-notes/
```

Feature note should include:

```text
Feature name
What was implemented
Why this design
Key files
Tests
Interview talking points
Limitations
Follow-up work
```

Do not paste raw AI output.

Rewrite into concise engineering notes.

---

## 12. When Planning Can Be Skipped

Planning can be skipped for:

- typo fixes;
- formatting-only changes;
- one-line bug fixes;
- adding a short comment;
- small documentation edits.

Planning should not be skipped for:

- schema changes;
- LangGraph changes;
- routing changes;
- test strategy changes;
- evaluation changes;
- dependency changes;
- LLM integration;
- tool calling;
- human review behavior.

---

## 13. Repeated Mistake Rule

If Codex makes the same mistake twice, update one of:

- `AGENTS.md`
- `docs/ai-coding-workflow.md`
- `docs/code-review-checklist.md`
- relevant future skill file under `.agents/skills/`

The goal is to convert repeated friction into durable guidance.
