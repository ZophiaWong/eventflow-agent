# Architecture Docs

This folder contains architecture documents for EventFlow Agent.

The goal of these documents is to keep system design clear and maintainable as the project evolves from an MVP into a more complete Agentic Workflow system.

## Documents

### `architecture-overview.md`

High-level system architecture, workflow, component responsibilities, LangGraph usage, MVP architecture, and extension plan.

Start here if you want to understand the system end-to-end.

### `data-model.md`

Planned document for core data models and schemas.

Expected topics:

- RawSignal
- EventCandidate
- EventCluster
- EvidencePack
- RiskAssessment
- HumanReviewDecision
- EventRiskBrief

### `state-design.md`

Planned document for LangGraph state design.

Expected topics:

- state fields;
- node read/write responsibilities;
- route decision fields;
- error handling;
- metrics;
- audit log structure.

### `graph-design.md`

Planned document for LangGraph workflow details.

Expected topics:

- nodes;
- edges;
- conditional routing;
- human review interruption;
- retry and fallback paths;
- checkpoint and resume behavior.

### `action-layer.md`

Planned document for future action recommendation and controlled tool calling.

Expected topics:

- action types;
- tool policy checks;
- human approval rules;
- side-effecting action boundaries;
- controlled remediation roadmap.

## Recommended Reading Order

1. `../../README.md`
2. `architecture-overview.md`
3. `data-model.md`
4. `state-design.md`
5. `graph-design.md`
6. `action-layer.md`
7. `../project-roadmap.md`

## Maintenance Rules

- Keep `architecture-overview.md` focused on high-level architecture.
- Put schema details in `data-model.md`.
- Put LangGraph state details in `state-design.md`.
- Put node and edge details in `graph-design.md`.
- Put tool calling and remediation details in `action-layer.md`.
- Prefer links over duplicating the same explanation across multiple files.
- Update architecture docs only when an implemented design or committed design decision changes.
