# EventFlow Agent

**LangGraph-based Agentic Workflow for SaaS External Event Triage**

> Status: M0 — Project Setup & Design Contract.

## Overview

EventFlow Agent is a prototype AI Agent workflow that models how a SaaS team triages external events such as service incidents, security advisories, API changes, and product releases.

The system convert noisy signals into structured risk assessments and controlled next-step recommendations. The MVP starts with an offline-first workflow using sample data and simulated SaaS business context. Later versions may extend the workflow with approved tool calling and controlled remediation.

This project is designed as an engineering prototype. It does not claim real enterprise deployment, real customer impact, or production metrics.

## Problem

Modern SaaS products depend on many external services, APIs, SDKs, cloud platforms, and open-source components.

Examples include:

- cloud platforms such as AWS, GCP, or Azure;
- source control and CI/CD tools such as GitHub and GitHub Actions;
- payment providers such as Stripe;
- AI APIs such as OpenAI or Anthropic;
- deployment platforms such as Vercel or Render;
- open-source libraries such as FastAPI, Pydantic, LangGraph, or PostgreSQL-related packages.

These dependencies produce external signals across status pages, release notes, security advisories, GitHub releases, vendor blogs, RSS feeds, and changelogs.

The challenge is not simply reading these updates. The challenge is deciding whether an external signal actually matters to a specific product or team:

## What It Does

The planned MVP supports the following capabilities:

- load sample external event signals;
- normalize source-specific data into a shared schema;
- classify event types;
- deduplicate similar events;
- retrieve dependency context, playbooks, and historical cases;
- assess risk level and confidence;
- route high-risk or low-confidence cases to human review;
- generate an Event Risk Brief;
- prepare the workflow for future action recommendation and tool calling.

An Event Risk Brief is a structured workflow output that contains the event summary, affected dependencies, evidence references, risk level, rationale, recommended action, and review status.

## Core Workflow

```text
Raw Signal
-> Normalized Signal
-> Classify Event
-> Deduplicate / Merge
-> Retrieve Evidence
-> Assess Risk
-> Human Review if Needed
-> Generate Event Risk Brief
-> Optional Action Layer
```

## MVP Scope

### In Scope

- sample external event data;
- structured Pydantic schemas;
- event normalization;
- event classification;
- simple deduplication;
- dependency map lookup;
- playbook and historical case retrieval;
- risk assessment;
- human review routing;
- Event Risk Brief generation;
- basic tests and evaluation planning.

### Out of Scope

- real-time data ingestion;
- production alerting;
- real enterprise data;
- multi-tenant authentication;
- complex UI dashboard;
- direct production remediation;
- unrestricted autonomous tool execution.

## Architecture

The architecture is organized around a stateful LangGraph workflow. Each step reads and writes structured state, and routing decisions are made through explicit conditional edges.

For details, see:

- [Architecture Overview](docs/architecture/architecture-overview.md)
- [Architecture Docs Index](docs/architecture/README.md)

## Tech Stack

Planned stack:

- Python
- LangGraph
- Pydantic
- FastAPI
- pytest
- LangSmith or local structured tracing
- SQLite or PostgreSQL for structured data
- pgvector or Chroma for retrieval experiments in later stages
- Docker in later stages

## Quick Start

The project is currently in M0. It provides a minimal Python package skeleton and a smoke test.

Development commands:

```bash
# create a local virtual environment
python3 -m venv .venv

# install the package with development test dependencies
.venv/bin/python -m pip install -e ".[dev]"

# run tests
.venv/bin/python -m pytest
```

## Roadmap

| Stage | Goal                                                                          |
| ----- | ----------------------------------------------------------------------------- |
| M0    | Project setup, design contract, documentation structure, AI coding guardrails |
| M1    | Data model and sample dataset                                                 |
| M2    | Rule-based baseline workflow                                                  |
| M3    | LangGraph workflow MVP                                                        |
| M4    | Agentic RAG / evidence retrieval                                              |
| M5    | Human-in-the-loop review                                                      |
| M6    | Replay evaluation and project polish                                          |
| V1    | Action recommendation                                                         |
| V2    | Tool calling with approval                                                    |
| V3    | Controlled remediation                                                        |

Detailed roadmap will be maintained in `docs/project-roadmap.md`.

## Documentation

Planned documentation:

- `docs/project-roadmap.md` — project milestones and completion criteria;
- `docs/architecture/` — architecture, data model, state design, and graph design;
- `docs/project-notes/` — project notes, technical decisions, interview-oriented Q&A, and feature notes.

## Limitations

This is an offline-first prototype. It uses sample data and simulated SaaS business context.

The MVP does not connect to real production systems, does not execute real remediation actions, and does not claim production reliability.

The purpose of the project is to demonstrate a controlled AI Agent workflow design: structured state, evidence-backed risk assessment, human review, and safe extension toward tool calling.
