# Interview Preparation Notes

This folder contains interview-oriented notes for EventFlow Agent.

The goal is to keep project explanation, and technical decisions, resume bullets, and feature-level learnings organized as the project evolves.

这里可以放一些面试相关的资料，比如在面试中可能会讲的架构设计、业务场景、技术栈、项目决策的理由等。

项目介绍：简短的项目描述，包含项目目标、业务场景、技术栈等。
技术决策：你在项目开发过程中做出的关键技术决策，比如为什么选择 LangGraph，为什么设计这样一个工作流。
架构设计：详细描述系统架构、每个模块的职责、如何使用 LangGraph 编排工作流、事件的流转过程。
测试与优化：展示你如何保证系统稳定性和性能，包括如何进行单元测试、集成测试、性能测试等。
可能的问题与回答：列出可能的面试问题并提前准备好答案。例如，“为什么需要引入人工审核？” “如何保证事件流转的稳定性？” 等。

---

## Files

### `project-pitch.md`

Short project explanations for interviews.

Recommended sections:

- 30-second pitch
- 1-minute pitch
- 3-minute pitch
- project positioning
- project limitations

---

### `technical-decisions.md`

Key engineering decisions and trade-offs.

Examples:

- why LangGraph;
- why rule-based baseline first;
- why Human-in-the-loop;
- why offline-first MVP;
- why Event Risk Brief before tool calling.

### `resume-bullets.md`

Draft resume bullets for different project stages.

Update this file only when an implementation milestone is completed.

---

### `feature-notes/`

Feature-level learning notes.

Each feature note should explain:

- what was implemented;
- why it was implemented this way;
- how it was tested;
- what interview talking points it creates;
- what limitations remain.

---

## Maintenance Rules

1. Do NOT paste raw AI-generated notes into this folder.
2. Keep each file responsible for one purpose.
3. Do NOT duplicate the same explanation across multiple files.
4. After completing a feature, add one feature note and update at most one high-level file.
5. Keep answer honest. Do NOT claim real production deployment or real business metrics unless they exist.
6. If a file grows too long, move detailed content into `feature-notes/`.
7. Every feature note should be tied to an actual implementation, test, or design decision.

---

## Recommended Update Flow

After each feature:

1. Run `interview-extraction` skill
2. Create or update one file in feature-notes/
3. Add only reusable high-level points to `interview-qa.md`
4. Add resume-ready bullets only after the feature is implemented and tested
