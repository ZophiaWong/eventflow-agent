# EventFlow Agent

**基于 LangGraph 的 SaaS 外部事件 Triage Agentic Workflow**

> Status: M4 — Evidence Retrieval / Agentic RAG MVP。

## Overview

EventFlow Agent 是一个 AI Agent workflow 原型项目，用于模拟 SaaS 团队如何 triage 外部事件，例如 service incident、security advisory、API change 和 product release。

系统会将分散且噪声较高的外部信号转化为结构化风险判断和受控的下一步动作建议。MVP 采用 offline-first 的方式，基于 sample data 和模拟 SaaS 业务上下文来实现核心 workflow。后续版本可以扩展到经过审批的 tool calling 和 controlled remediation。

这是一个工程原型项目，不声明真实企业上线、真实客户影响或生产环境指标。

## Problem

现代 SaaS 产品通常依赖大量外部服务、API、SDK、cloud platform 和 open-source components。

常见例子包括：

- AWS、GCP、Azure 等 cloud platform；
- GitHub、GitHub Actions 等 source control 和 CI/CD 工具；
- Stripe 等支付服务；
- OpenAI、Anthropic 等 AI API；
- Vercel、Render 等部署平台；
- FastAPI、Pydantic、LangGraph、PostgreSQL 相关 package 等 open-source libraries。

这些依赖会持续在 status page、release notes、security advisories、GitHub releases、vendor blogs、RSS feeds 和 changelogs 中产生外部信号。

真正困难的地方不是简单阅读这些更新，而是判断某个外部信号是否真的影响具体产品或团队：

- 这个事件是否影响了我们的某个 dependency？
- 它是 service incident、security advisory、API change，还是普通 product release？
- 哪个 product area 可能受到影响？
- 风险等级有多高？
- 团队应该 ignore、watch、notify support、create issue，还是 escalate to engineering？
- 当前证据是否足够，还是需要 human review？

EventFlow Agent 将这个 triage 过程建模为一个 stateful Agentic Workflow。

## What It Does

计划中的 MVP 支持以下能力：

- 加载 sample external event signals；
- 将不同来源的数据 normalize 为统一 schema；
- 对 event type 进行 classification；
- 对相似事件进行 deduplication；
- 检索 dependency context、playbooks 和 historical cases；
- 评估 risk level 和 confidence；
- 将 high-risk 或 low-confidence case 路由到 human review；
- 生成 Event Risk Brief；
- 为后续 action recommendation 和 tool calling 预留 workflow 扩展点。

**Event Risk Brief** 是 workflow 的结构化输出，包含事件摘要、affected dependencies、evidence references、risk level、判断理由、recommended action 和 review status。

## Core Workflow

```text
Raw Signal
→ Normalize Signal
→ Classify Event
→ Deduplicate / Merge
→ Retrieve Evidence
→ Assess Risk
→ Human Review if Needed
→ Generate Event Risk Brief
→ Optional Action Layer
```

## MVP Scope

### In Scope

- sample external event data；
- structured Pydantic schemas；
- event normalization；
- event classification；
- simple deduplication；
- dependency map lookup；
- playbook 和 historical case retrieval；
- risk assessment；
- human review routing；
- Event Risk Brief generation；
- basic tests 和 evaluation planning。

### Out of Scope

- real-time data ingestion；
- production alerting；
- real enterprise data；
- multi-tenant authentication；
- complex UI dashboard；
- direct production remediation；
- unrestricted autonomous tool execution。

## Architecture

系统架构围绕 stateful LangGraph workflow 组织。每个步骤都会读取和写入结构化 state，路由决策通过明确的 conditional edges 完成。

详细内容见：

- [Architecture Overview](docs/architecture/architecture-overview.md)
- [Architecture Docs Index](docs/architecture/README.md)

## Tech Stack

计划中的技术栈：

- Python
- LangGraph
- Pydantic
- FastAPI
- pytest
- LangSmith 或 local structured tracing
- SQLite 或 PostgreSQL 用于 structured data
- 后续阶段使用 pgvector 或 Chroma 做 retrieval experiments
- 后续阶段引入 Docker

## Quick Start

项目当前包含 typed schemas、synthetic sample data、deterministic rule-based baseline workflow、LangGraph StateGraph MVP，以及带 retrieval quality scoring 的 structured local evidence retrieval。

开发命令：

```bash
# create a local virtual environment
python3 -m venv .venv

# install the package with development test dependencies
.venv/bin/python -m pip install -e ".[dev]"

# run tests
.venv/bin/python -m pytest

# run one sample signal through the baseline
.venv/bin/python -m eventflow.baseline --signal-id sig_001 --data-dir data --pretty

# run draft baseline eval smoke metrics
.venv/bin/python -m eventflow.baseline --eval --data-dir data --pretty
```

## Roadmap

| Stage | Goal                                                                          |
| ----- | ----------------------------------------------------------------------------- |
| M0    | Project setup、design contract、documentation structure、AI coding guardrails |
| M1    | Data model and sample dataset                                                 |
| M2    | Rule-based baseline workflow                                                  |
| M3    | LangGraph workflow MVP                                                        |
| M4    | Agentic RAG / evidence retrieval                                              |
| M5    | Human-in-the-loop review                                                      |
| M6    | Replay evaluation and project polish                                          |
| V1    | Action recommendation                                                         |
| V2    | Tool calling with approval                                                    |
| V3    | Controlled remediation                                                        |

详细 roadmap 会维护在 `docs/project-roadmap.md`。

## Documentation

计划中的文档：

- `docs/project-roadmap.md` — 项目 milestone 和 completion criteria；
- `docs/architecture/` — architecture、data model、state design 和 graph design；
- `docs/project-notes/` — project notes、technical decisions、interview-oriented Q&A 和 feature notes。

## Limitations

这是一个 offline-first 原型项目，使用 sample data 和模拟 SaaS 业务上下文。

MVP 不连接真实生产系统，不执行真实 remediation actions，也不声明 production reliability。

项目目标是展示一个受控的 AI Agent workflow 设计：structured state、evidence-backed risk assessment、human review，以及面向 tool calling 的安全扩展路径。
