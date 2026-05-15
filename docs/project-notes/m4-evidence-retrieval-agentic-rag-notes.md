# M4 Evidence Retrieval / Agentic RAG Notes

## 为什么 EventFlow 需要 evidence retrieval

EventFlow 的目标不是总结外部新闻，而是判断外部 SaaS 事件是否影响模拟产品中的具体 dependency。

风险判断必须有依据：

- dependency map 说明这个 vendor 是否被产品使用；
- playbook 说明该 event type 和 dependency criticality 下应该如何响应；
- historical case 提供类似 synthetic 事件的处理经验；
- source signal 保留当前事件的来源引用。

如果没有这些证据，workflow 不应该生成正常的 Event Risk Brief。

## 为什么不是通用知识库 Q&A

M4 retrieval 回答的是 triage 问题，不是开放式问答。

核心问题是：

- 是否命中已知 dependency；
- 影响哪个 product module；
- dependency criticality 是什么；
- 是否有匹配 playbook；
- 是否有类似 historical case；
- 当前 evidence 是否足够进入 risk assessment。

因此 M4 使用 structured retrieval，而不是让模型自由搜索或生成答案。

## 为什么先做 structured retrieval

M4 仍处于 MVP 阶段。优先选择 deterministic retrieval 有几个原因：

- 输入输出稳定，方便 unit test 和 graph path test；
- 可以清楚解释每个 routing decision；
- 避免把风险判断建立在不可复现的 prompt 行为上；
- 后续可以替换为 vector DB 或 hybrid retrieval，而不改变 graph contract。

## 为什么暂缓 vector DB 和 LLM judge

Vector DB 适合更大规模、非结构化文本检索，但当前 sample data 很小，dependency、playbook、historical case 都是结构化数据。

LLM judge 可以用于后续辅助判断 evidence relevance，但不应该成为 M4 的主路由依据。当前主路由使用 rule-based retrieval_quality，保证可测试和可复现。

## retrieval_quality 如何计算

M4 使用 retrieval design 中的加权公式：

```text
retrieval_quality =
  dependency_match_score * 0.4
+ playbook_match_score * 0.3
+ historical_case_score * 0.2
+ source_support_score * 0.1
```

阈值：

- `>= 0.70`：sufficient，可以进入 risk assessment；
- `0.45 - 0.70`：weak，不生成正常 brief；
- `< 0.45`：insufficient，不生成正常 brief。

硬性规则：

```text
dependency_match_score == 0
→ insufficient
```

原因是 EventFlow 必须先确认外部事件是否影响模拟产品中的 dependency。

## retrieval failure 和 weak evidence 的区别

Retrieval failure 是系统无法执行检索，例如 required state 缺失或 retrieval code 抛出异常。

结果：

```text
route_decision = error
errors populated
no normal EventRiskBrief
```

Weak evidence 是检索正常完成，但证据不足以支持风险判断。

结果：

```text
route_decision = request_more_evidence
errors empty
missing_evidence_reasons populated
no normal EventRiskBrief
```

这个区别很重要：前者是 workflow failure，后者是业务证据不足。

## Agentic RAG 在 M4 中如何体现

M4 的 Agentic RAG 不是无限 autonomous search，而是一个小型可控 loop：

```text
EventCluster
→ RetrievalQuery
→ retrieve dependency/playbook/historical evidence
→ build EvidencePack
→ evaluate evidence quality
→ route to assess_risk or request_more_evidence
```

当前实现先完成最小闭环。Rule-based query rewrite 可以作为后续增强，但不影响 M4 的核心价值。

## 对 risk assessment、evaluation 和 future tool calling 的价值

Risk assessment 不再自己做 retrieval，而是消费 `EvidencePack`。

这样带来三个好处：

- risk rationale 可以引用明确 evidence refs；
- replay evaluation 可以检查 retrieval quality 和 missing evidence；
- future tool calling 可以要求 action proposal 必须建立在 sufficient evidence 之上。

## 常见面试问答

**Q: 为什么不直接用 LLM 判断风险？**

A: 这个项目强调 controlled Agent workflow。M4 先用 deterministic evidence retrieval 建立可测试基线，再考虑 LLM 增强。否则风险判断很难复现和评估。

**Q: 为什么 dependency match 权重最高？**

A: EventFlow 关注的是外部事件是否影响本产品。如果 vendor 不在 dependency map 中，即使有 generic playbook，也不应该 confident 地评估产品风险。

**Q: historical case 没有命中是否一定失败？**

A: 不是。Historical case 是辅助上下文。只要 dependency、playbook 和 source support 足够强，仍然可以进入 risk assessment。

**Q: M4 的 RAG 为什么没有 vector DB？**

A: 当前数据是小规模结构化 sample data，规则检索更简单、更可测。Vector DB 属于后续规模化或非结构化文本检索场景。

**Q: request_more_evidence 为什么不是 error？**

A: 因为 workflow 正常执行了，只是证据不足。把它和系统错误区分开，才能让 graph routing、audit log 和 evaluation 更准确。
