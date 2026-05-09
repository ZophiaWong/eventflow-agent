# Code Review Checklist

Use this checklist before accepting AI-generated code or any non-trivial implementation change.

---

## 1. Scope

- [ ] Does the change match the requested task?
- [ ] Does it follow the current milestone in `docs/project-roadmap.md`?
- [ ] Does it avoid implementing future roadmap items early?
- [ ] Does it avoid modifying unrelated files?
- [ ] Is the diff small enough to review?
- [ ] Are assumptions stated clearly?

---

## 2. Architecture

- [ ] Does the change fit `docs/architecture/architecture-overview.md`?
- [ ] Does it preserve workflow-first design?
- [ ] Does it avoid turning the project into a generic chatbot?
- [ ] Does it avoid unnecessary abstraction?
- [ ] Does it keep graph logic separate from API or CLI logic?

---

## 3. Schema Safety

- [ ] Are core artifacts represented by Pydantic schemas?
- [ ] Does the code avoid long-lived untyped dictionaries?
- [ ] Are invalid inputs handled explicitly?
- [ ] Are schema changes covered by tests?
- [ ] If LLM output is used, is it validated before entering workflow state?

---

## 4. LangGraph State Safety

- [ ] Are state fields explicit?
- [ ] Does each node have clear read/write responsibilities?
- [ ] Is routing logic explicit and testable?
- [ ] Are route decisions recorded where appropriate?
- [ ] Are hidden state mutations avoided?
- [ ] Is graph construction separated from node implementation?

---

## 5. Evidence and Risk Logic

- [ ] Does risk assessment use evidence where appropriate?
- [ ] Are unsupported claims avoided?
- [ ] Are evidence references preserved?
- [ ] Is missing evidence handled explicitly?
- [ ] Are low-confidence cases routed safely?
- [ ] Are high-risk cases routed to review when review logic exists?

---

## 6. Human-in-the-loop and Tool Safety

- [ ] Are high-risk decisions reviewable?
- [ ] Are side-effecting actions avoided in MVP?
- [ ] Are future tool calls gated by policy and approval?
- [ ] Is reviewer decision behavior explicit?
- [ ] Are approve, reject, and request-more-evidence paths considered where relevant?

---

## 7. Tests

- [ ] Are unit tests added or updated?
- [ ] Are integration tests added or updated for graph changes?
- [ ] Are routing paths tested?
- [ ] Are error cases tested?
- [ ] Are external calls mocked?
- [ ] Do tests avoid requiring real secrets or live services?
- [ ] Are tests aligned with the current milestone?

---

## 8. Documentation

- [ ] Is README kept concise?
- [ ] Are architecture changes documented in `docs/architecture/`?
- [ ] Are roadmap changes reflected in `docs/project-roadmap.md` if needed?
- [ ] Are project notes updated only when useful?
- [ ] Is raw AI output avoided in docs?
- [ ] Are claims consistent with actual implementation status?

---

## 9. Dependencies and Security

- [ ] Were new dependencies avoided unless necessary?
- [ ] If dependencies were added, is the reason documented?
- [ ] Are secrets avoided?
- [ ] Is `.env.example` used instead of real secrets?
- [ ] Is real company or customer data avoided?
- [ ] Are file writes or external actions explicit?
- [ ] Are side effects controlled?

---

## 10. Verification

- [ ] Were relevant tests run?
- [ ] Were lint or type checks run if configured?
- [ ] Are failed or skipped checks explained?
- [ ] Does the final summary accurately report validation?
- [ ] Are known gaps stated?
- [ ] Is there a clear next step?

---

## 11. Interview Explainability

- [ ] Can the developer explain why this change exists?
- [ ] Can the developer explain the trade-off?
- [ ] Can the developer explain how it was tested?
- [ ] Can the developer explain how it fits the roadmap?
- [ ] Can the developer explain what remains incomplete?
- [ ] Can the developer discuss how this would be productionized later?
