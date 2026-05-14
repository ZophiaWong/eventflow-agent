# M3 LangGraph Workflow Interview Notes

这份文档用于帮助自己理解和讲清楚 EventFlow Agent 的 LangGraph workflow 设计。

它不是工程契约文档。工程设计以以下文件为准：

```text
docs/architecture/state-design.md
docs/architecture/graph-design.md
```

这份文档主要服务于：

```text
理解设计
复盘取舍
准备面试表达
沉淀常见追问回答
```

---

## 1. 这个阶段实现了什么？

这个阶段的核心目标是：

> 把原来的 rule-based baseline workflow 迁移成 LangGraph StateGraph。

也就是说，不再只是写一条普通 Python pipeline：

```text
load signal
→ classify
→ assess risk
→ generate brief
```

而是把事件处理拆成明确的 graph 节点：

```text
normalize_signal
→ classify_event
→ deduplicate_event
→ retrieve_evidence
→ assess_risk
→ conditional routing
→ generate_event_risk_brief
```

这个阶段重点展示的是：

```text
StateGraph
workflow state
node-level responsibilities
conditional routing
error path
human review placeholder
graph path tests
```

它不是要一次性实现完整 Agent 系统。

---

## 2. 为什么从 baseline 迁移到 LangGraph？

baseline workflow 的好处是简单、确定、容易测试。

但它的问题是：

```text
流程是固定的
不适合复杂分支
人审和 retry 不自然
后续 interrupt/resume 不好接
不同路径的测试表达不够清晰
```

EventFlow 的事件处理不是永远走同一条路。

它需要根据 state 决定：

```text
低风险事件 → 自动生成 brief
高风险事件 → 进入 human review
证据不足 → request more evidence
状态错误 → error path
```

所以用 LangGraph 的价值在于：

> 把事件处理从固定 pipeline 变成显式状态机。

面试表达可以这样说：

> 我先做 rule-based baseline，是为了建立确定性参考。M3 再迁移到 LangGraph，是因为这个系统开始需要 conditional routing、状态化执行和可测试的 graph path。LangGraph 不是为了炫技，而是因为事件 triage 本身有不同路径。

---

## 3. State 是怎么设计的？

State 可以理解为：

> 一次事件处理过程中，graph 携带的完整上下文。

它不是单个业务对象，而是一次 workflow run 的运行时容器。

比如：

```text
raw_signal
event_candidate
event_cluster
evidence_pack
risk_assessment
event_risk_brief
route_decision
errors
audit_log
```

这些字段表示：

```text
当前处理的是哪条外部信号？
系统理解成了什么事件？
有没有找到证据？
风险判断是什么？
最终走了哪条路径？
有没有错误？
每个节点做了什么？
```

可以这样理解：

```text
Data Model = 单个业务对象
Workflow State = 一次 graph run 的完整上下文
```

---

## 4. 为什么 State 用 TypedDict，业务对象用 Pydantic？

这是一个很重要的设计点。

业务对象用 Pydantic，例如：

```text
RawSignal
EventCandidate
EvidencePack
RiskAssessment
EventRiskBrief
```

原因是这些对象需要：

```text
字段校验
枚举约束
confidence 范围校验
sample data validation
测试稳定性
```

而 LangGraph 的整体 State 用 TypedDict，原因是：

```text
State 是运行时容器
不同阶段字段会逐步出现
节点只返回 partial state update
TypedDict 更轻量
更符合 LangGraph 常见用法
```

也就是说：

```text
Pydantic 负责业务对象的 correctness
TypedDict 负责 workflow state 的 shape
```

面试表达：

> 我没有把整个 workflow state 做成一个巨大的 Pydantic model，因为 graph 执行过程中很多字段是逐步产生的。业务对象需要严格 validation，所以用 Pydantic；state 作为运行时容器，用 TypedDict 更自然。

---

## 5. 每个 node 的职责是什么？

这个阶段的 node 设计原则是：

> 一个 node 只做一件事，只写自己负责的 state 字段。

主要节点：

### `normalize_signal_node`

负责确认输入 raw signal 是否可用。

它读：

```text
raw_signal
```

它写：

```text
audit_log
errors if invalid
```

---

### `classify_event_node`

负责把 RawSignal 转成 EventCandidate。

它读：

```text
raw_signal
```

它写：

```text
event_candidate
audit_log
```

---

### `deduplicate_event_node`

负责生成 EventCluster。

当前可以只做 minimal cluster，也就是把单个 EventCandidate 包装成一个 EventCluster。

它读：

```text
event_candidate
```

它写：

```text
event_cluster
audit_log
```

---

### `retrieve_evidence_node`

负责根据 event_cluster 查 dependency map、playbook、historical cases。

当前只做 sample lookup，不做完整 RAG。

它读：

```text
event_cluster
```

它写：

```text
evidence_pack
audit_log
```

---

### `assess_risk_node`

负责根据 event_cluster 和 evidence_pack 判断风险。

它读：

```text
event_cluster
evidence_pack
```

它写：

```text
risk_assessment
audit_log
```

---

### `route_after_risk_assessment`

这是 conditional routing function。

它读：

```text
errors
evidence_pack
risk_assessment
```

它决定下一步走：

```text
auto_brief
human_review
request_more_evidence
error
```

---

### `generate_event_risk_brief_node`

负责生成最终 EventRiskBrief。

它读：

```text
event_cluster
evidence_pack
risk_assessment
human_review_decision optional
```

它写：

```text
event_risk_brief
audit_log
```

---

## 6. conditional routing 是怎么设计的？

conditional routing 的设计逻辑是：

```text
if errors exist:
    error

else if evidence is missing or retrieval quality is too low:
    request_more_evidence

else if risk_assessment.requires_human_review:
    human_review

else:
    auto_brief
```

这个顺序很重要。

### 为什么 error 优先？

因为如果 workflow 已经出现结构化错误，例如缺少 raw_signal 或 risk_assessment，就不应该继续生成正常 brief。

---

### 为什么 evidence 不足不是 error？

这是一个关键点。

如果 evidence lookup 失败，比如代码出错、文件不存在，那是 error。

但如果 lookup 成功，只是证据不足，那不是系统失败，而是业务状态：

```text
request_more_evidence
```

所以：

```text
retrieval failure != insufficient evidence
```

这能体现设计的严谨性。

---

### 为什么 human review 是 route，而不是直接执行？

因为高风险事件不应该自动完成决策。

当前阶段只标记：

```text
route_decision = human_review
review_status = pending
```

真正的人审 interrupt/resume 放到后续阶段。

---

## 7. 为什么 human review 现在只是 placeholder？

因为当前阶段的目标是验证 LangGraph workflow 和 conditional routing，不是完整实现 Human-in-the-loop。

真正的 Human-in-the-loop 需要：

```text
checkpointer
thread_id
interrupt
resume payload
review API or UI
review decision schema
approval / edit / reject handling
```

这些会显著增加复杂度。

所以当前阶段只做：

```text
高风险事件 route 到 human_review_placeholder
生成 pending review brief
不创建 fake HumanReviewDecision
不假装人类已经审核
```

这是一个有意的 scope control。

面试表达：

> 我没有在 M3 直接实现 interrupt/resume，因为那会把 checkpoint、thread_id、review payload、API/UI 都拉进来。当前目标是先验证 graph routing。真正 Human-in-the-loop 放到后续专门阶段实现，这样可以保持每个阶段聚焦。

---

## 8. 为什么 evidence retrieval 现在不是完整 RAG？

当前阶段的重点是 LangGraph workflow，不是 RAG。

所以 evidence retrieval 先做：

```text
dependency_map lookup
playbook lookup
historical_cases lookup
```

也就是 sample lookup / rule-based lookup。

这样可以先证明：

```text
event_cluster → evidence_pack → risk_assessment
```

这个状态链路是成立的。

后续再把 retrieval 升级成：

```text
Agentic RAG
query rewriting
retrieval quality evaluation
historical case semantic retrieval
```

面试表达：

> 我把 retrieval 分阶段做。M3 只做 sample lookup，是为了验证 evidence_pack 这个状态和 risk_assessment 的依赖关系。M4 再升级成 Agentic RAG，这样可以避免把 workflow 和 retrieval complexity 混在一起。

---

## 9. 为什么 dedup 现在只做 minimal cluster？

Dedup 是一个很容易变复杂的模块。

完整 dedup 可能涉及：

```text
title similarity
time window
vendor matching
embedding similarity
LLM merge judge
cluster update
duplicate confidence
```

但当前阶段的核心不是 dedup 算法，而是 graph workflow。

所以现在可以先做：

```text
single EventCandidate → single EventCluster
```

这样能让后续节点统一读取 EventCluster，而不必现在实现复杂 clustering。

面试表达：

> 我先把 EventCluster 作为统一接口引入，但 dedup 算法先保持最小实现。这样后续可以逐步升级 dedup，而不会影响 retrieve_evidence 和 assess_risk 的接口。

---

## 10. audit_log 和 errors 的作用是什么？

### `errors`

`errors` 用来保存 workflow 运行中的结构化错误。

例如：

```text
missing_raw_signal
classification_failed
evidence_lookup_failed
risk_assessment_failed
brief_generation_failed
```

它的作用是：

```text
让 graph 不只是抛异常
让错误路径可测试
让 route function 能判断是否进入 error path
```

---

### `audit_log`

`audit_log` 是轻量 workflow trace。

它记录：

```text
哪个 node 执行了
执行结果是什么
输入/输出对象 ID 是什么
是否产生 route_decision
有没有 error_code
```

它不记录：

```text
完整 prompt
hidden reasoning
大段 raw content
敏感数据
```

它的作用是：

```text
debug
route inspection
replay analysis
test assertion
```

面试表达：

> audit_log 不是完整 observability 平台，而是轻量结构化 trace。它能帮助我知道事件是在哪个节点被分类、在哪个节点判断高风险、为什么进入 human_review 或 request_more_evidence。

---

## 11. 这个设计如何支持后续 RAG / HITL / Evaluation / Tool Calling？

### 支持 RAG

因为 workflow 中已经有：

```text
retrieve_evidence_node
evidence_pack
retrieval_quality
```

所以后续可以把 sample lookup 替换成 Agentic RAG，而不需要重写整个 graph。

---

### 支持 Human-in-the-loop

因为现在已经有：

```text
human_review route
human_review_placeholder
review_status = pending
human_review_decision field
```

所以后续可以把 placeholder 替换成真实 interrupt/resume。

---

### 支持 Evaluation

因为 state 中有：

```text
route_decision
risk_assessment
event_risk_brief
errors
audit_log
```

所以可以做 replay evaluation：

```text
expected_event_type
expected_risk_level
expected_route
expected_recommended_action
```

---

### 支持 Tool Calling

因为当前没有把 tool calling 嵌进核心 triage nodes。

未来可以在 EventRiskBrief 后面接：

```text
action proposal
policy check
human approval
tool execution
audit log
```

这样更安全。

---

## 12. 面试官可能追问的问题

---

## Q1: 为什么用 LangGraph？普通 pipeline 不行吗？

可以回答：

> 普通 pipeline 可以处理固定线性流程，但 EventFlow 需要根据风险、证据和错误状态做不同路由。低风险事件自动生成 brief，高风险事件进入 human review，证据不足时 request more evidence，状态错误时进入 error path。LangGraph 能把这些状态、节点和 conditional routing 显式化，并且方便写 graph path tests。

---

## Q2: 为什么不一开始就做完整 Human-in-the-loop？

可以回答：

> 我把它拆到后续阶段，是为了控制复杂度。完整 HITL 需要 checkpointer、thread_id、interrupt/resume、review payload 和 reviewer API/UI。当前阶段先做 human_review_placeholder，验证 routing 逻辑。等 graph 稳定后再把 placeholder 替换成真实 interrupt/resume。

---

## Q3: 为什么 State 用 TypedDict，不是全部用 Pydantic？

可以回答：

> 业务对象用 Pydantic，因为它们需要字段校验和 sample data validation。Graph state 是运行时容器，字段会随着节点执行逐步出现，节点也只返回 partial updates，所以用 TypedDict 更轻量。这个组合能同时保持 validation 和 graph 灵活性。

---

## Q4: 你怎么保证 graph 不是一堆节点乱连？

可以回答：

> 我用 state-design 和 graph-design 分别约束“state 里有什么”和“graph 怎么走”。每个字段有 owner node，每个 node 有明确 read/write，conditional routing 只根据 errors、evidence_pack、risk_assessment 决定。这样每个节点职责清楚，路径也可测试。

---

## Q5: audit_log 有什么用？

可以回答：

> audit_log 是轻量结构化 trace。它记录哪个 node 做了什么、输入输出对象 ID、route_decision 和 error_code。这样可以 debug workflow，也可以在 replay evaluation 中检查 graph 是否走了预期路径。它不是完整 tracing 系统，也不记录隐藏推理或敏感内容。

---

## Q6: 你如何测试这个 graph？

可以回答：

> 我按 graph path 测试，而不是只测 happy path。至少覆盖 low-risk auto brief、high-risk human review placeholder、missing evidence request_more_evidence、invalid input error path。这样可以验证 conditional routing 是否按预期工作。

---

## Q7: request_more_evidence 和 error 有什么区别？

可以回答：

> error 表示 workflow 执行失败，比如缺少 required state 或 evidence lookup 报错。request_more_evidence 表示 workflow 正常运行，但证据不足，无法做可靠判断。两者分开可以避免把业务不确定性当成系统错误。

---

## Q8: 为什么现在的 evidence retrieval 不是 Agentic RAG？

可以回答：

> 当前阶段重点是 LangGraph workflow，所以 retrieval 先用 sample lookup。这样可以先验证 evidence_pack 和 risk_assessment 的状态流。后续再把 lookup 替换成 Agentic RAG，比如 query rewriting、semantic retrieval、retrieval quality evaluation。

---

## Q9: 为什么 dedup 现在很简单？

可以回答：

> 因为当前阶段重点不是 dedup 算法，而是 graph workflow。先引入 EventCluster 作为统一接口，dedup 先做 single-candidate cluster。后续可以升级成 title similarity、embedding similarity 或 LLM merge judge，而不会影响下游接口。

---

## Q10: 这个设计如何避免 Agent 乱执行动作？

可以回答：

> 当前 graph 根本不执行 side-effecting tool calls。它只生成 EventRiskBrief 或进入 review/request_more_evidence/error route。未来 tool calling 会放在 brief 之后，并经过 action proposal、policy check、human approval 和 audit log。这是刻意的安全边界设计。

---

## 13. 一句话总结

可以这样总结 M3：

> M3 的核心是把 EventFlow 从线性 baseline 迁移成 LangGraph StateGraph。State 保存事件处理上下文，nodes 负责局部状态更新，conditional routing 根据 errors、evidence 和 risk assessment 选择路径。当前版本先用 placeholder 表示 human review 和 request_more_evidence，避免过早引入 interrupt/resume 和完整 RAG 复杂度。
