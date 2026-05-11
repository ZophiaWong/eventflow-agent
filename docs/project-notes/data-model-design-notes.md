# Data Model Design Notes

这是一份学习文档，用来解释 EventFlow Agent 的 data model 为什么这样设计。

它不是实现契约。真正指导代码实现的是：

```text
docs/architecture/data-model.md
```

这份文档的目标是帮助你理解：

- 为什么 Agent / Workflow 项目需要先做 data model；
- 如何从业务流程推导数据模型；
- 为什么 EventFlow Agent 需要 RawSignal、EventCandidate、EvidencePack、RiskAssessment 等模型；
- 以后遇到类似 Agent / RAG / Workflow 项目时，如何有一套自己的建模思路。

---

## 1. 为什么 Agent 项目需要认真做 data modeling？

很多初学者做 Agent 项目时，会直接从 prompt 或 LangGraph node 开始写。

比如：

```text
输入一段文本
让 LLM 判断风险
输出一段总结
```

这样很快能跑出 demo，但后面会遇到很多问题：

```text
输入格式不稳定
中间状态说不清楚
测试不好写
错误不好定位
人审不好接入
RAG 证据不好追踪
评估标准不好定义
面试时讲不清楚系统怎么工作
```

所以 data model 的作用是：

> 把开放式、模糊的 LLM workflow 变成结构化、可测试、可审计的工程系统。

对 AI Agent 工程师来说，data model 不是“数据库表设计”那么简单。它还决定了：

```text
workflow state 怎么流动
node 之间怎么传数据
工具调用结果怎么进入系统
LLM 输出怎么被校验
风险判断怎么被追踪
人类审核怎么恢复上下文
evaluation 怎么设计 gold labels
```

---

## 2. 建模时不要先想 class，要先想 workflow

一个常见错误是上来就问：

> 我要写哪些 class？

更好的方式是先问：

```text
系统输入是什么？
系统中间要做哪些判断？
每一步需要什么信息？
哪些信息要保留给后续节点？
哪些结果需要人工审核？
哪些字段要支持测试和 evaluation？
最终输出给谁看？
```

然后再从 workflow 反推 data model。

EventFlow Agent 的核心 workflow 是：

```text
外部原始信号
→ 系统初步理解
→ 去重合并
→ 检索证据
→ 风险判断
→ 人类审核
→ 最终风险简报
```

所以它自然对应：

```text
RawSignal
→ EventCandidate
→ EventCluster
→ EvidencePack
→ RiskAssessment
→ HumanReviewDecision
→ EventRiskBrief
```

这不是随便拆出来的，而是每个 model 都对应 workflow 中一个重要状态。

---

## 3. EventFlow 的数据流

可以把整个系统想成一个“逐步加工”的过程。

### 第一步：RawSignal

系统刚拿到的原始外部消息。

比如：

```text
GitHub Actions 出现 workflow job 启动延迟
Stripe API 发布了一个 breaking change
某个库发布了安全公告
```

这时候系统还没有真正理解它，只是保存原始输入。

---

### 第二步：EventCandidate

系统对 RawSignal 做了第一层理解。

比如：

```text
这是 service_incident
vendor 是 GitHub Actions
可能影响 CI/CD Pipeline
confidence 是 0.82
```

注意：EventCandidate 只是“候选理解”，不代表一定正确。

---

### 第三步：EventCluster

多个 RawSignal / EventCandidate 可能说的是同一件事。

比如：

```text
sig_001: GitHub Actions delayed jobs
sig_002: Update: GitHub Actions queues recovering
sig_003: Vendor blog mentions CI workflow delays
```

它们可能都属于同一个事件。

EventCluster 的作用就是把相关事件合并起来，避免重复处理。

---

### 第四步：EvidencePack

系统不能只靠当前事件文本判断风险。

它还需要查：

```text
我们是否依赖这个 vendor？
这个 dependency 是不是核心依赖？
playbook 里说这种事件怎么处理？
历史上类似事件怎么处理？
```

EvidencePack 就是这些证据的集合。

---

### 第五步：RiskAssessment

有了事件和证据后，系统开始判断：

```text
风险等级是什么？
置信度是多少？
为什么这么判断？
推荐动作是什么？
是否需要人审？
```

这一步是内部决策结果。

---

### 第六步：HumanReviewDecision

如果风险高、置信度低、证据不足，系统不能直接决定。

这时候进入 Human-in-the-loop。

HumanReviewDecision 记录人类的判断：

```text
approve
reject
edit
request_more_evidence
```

---

### 第七步：EventRiskBrief

最后输出一份给人看的结构化结果。

它回答：

```text
发生了什么？
影响什么？
证据是什么？
风险多高？
为什么？
建议做什么？
是否经过人审？
```

EventRiskBrief 是 MVP 的最终输出，也是未来 action layer 的输入。

---

## 4. 为什么要区分 RawSignal 和 EventCandidate？

这是一个非常重要的设计点。

你可能会问：

> 为什么不直接把原始消息解析成事件对象？为什么要分 RawSignal 和 EventCandidate？

原因是：

```text
RawSignal 是输入事实
EventCandidate 是系统解释
```

输入事实应该尽量原样保存。  
系统解释可能是错的。

比如 RawSignal 是：

```text
"Provider reports delayed workflow job starts."
```

系统可能解释为：

```text
event_type = service_incident
affected_dependency = GitHub Actions
```

但这个解释可能错：

```text
可能不是 service_incident
可能不是 GitHub Actions
可能只是普通 maintenance notice
```

如果把原始输入和系统解释混在一起，后面就很难判断：

```text
错误是来自原始数据？
还是来自分类逻辑？
还是来自 LLM extraction？
```

所以要分开。

这也是很多 Agent 系统中很重要的原则：

> 保留 raw input，单独保存 model / rule 的 interpretation。

---

## 5. 为什么需要 EventCluster？

外部事件经常不是一次性出现的。

一个服务故障可能会有：

```text
initial report
investigating update
mitigation update
resolved update
third-party summary
```

如果系统把每条都当成独立事件，就会造成：

```text
重复告警
重复人审
重复生成 brief
重复创建 issue
```

EventCluster 的作用是：

> 把多个相关 EventCandidate 合并成一个真实事件视角。

M1 只是定义这个模型，不一定马上做复杂 dedup。

后续可以逐步演进：

```text
M2: 简单规则去重
M3: LangGraph 中增加 dedup node
M4+: embedding similarity 或 LLM merge judge
```

---

## 6. 为什么需要 EvidencePack？

一个常见错误是让 RiskAssessment node 自己到处查数据，然后直接输出风险结果。

这样会有几个问题：

```text
风险判断为什么这样做不清楚
证据无法复用
测试很难写
brief 里无法引用证据
evaluation 不好判断 unsupported claim
```

EvidencePack 的作用是把“找证据”和“做判断”分开。

流程变成：

```text
retrieve evidence
→ build EvidencePack
→ assess risk using EvidencePack
```

这样有几个好处：

```text
可以单独测试 retrieval
可以单独测试 risk assessment
可以检查 risk rationale 是否有 evidence support
可以在 EventRiskBrief 中展示 evidence_refs
可以在 evaluation 中计算 unsupported_fact_rate
```

这也是 RAG 项目中很重要的设计：

> retrieval 结果应该是显式结构，而不是隐藏在 prompt 里。

---

## 7. 为什么 RiskAssessment 和 EventRiskBrief 要分开？

RiskAssessment 是内部判断。  
EventRiskBrief 是最终展示结果。

它们看起来很像，但职责不同。

### RiskAssessment 关心的是决策

例如：

```text
risk_level
confidence
risk_factors
uncertainty_factors
recommended_action
requires_human_review
rationale
```

它服务于：

```text
routing
human review
evaluation
tool calling policy
```

### EventRiskBrief 关心的是表达

例如：

```text
title
summary
affected_dependencies
evidence_refs
risk_rationale
recommended_action
review_status
```

它服务于：

```text
人类阅读
demo 展示
后续 action planning
```

分开的好处是：

```text
可以独立测试风险逻辑
可以修改 brief 文案而不影响风险判断
可以保留人审前后的判断差异
可以避免 UI/展示层污染核心决策层
```

这是一个很实用的工程设计原则：

> internal decision model 和 user-facing output model 不要混在一起。

---

## 8. 为什么需要 HumanReviewDecision？

Agent 系统最容易被质疑的一点是：

> 你怎么保证它不会乱执行高风险动作？

HumanReviewDecision 的作用是明确：

```text
哪些事情由系统判断
哪些事情必须由人类确认
人类做了什么修改
最终是否批准
```

这对未来 tool calling 很重要。

比如未来 V2 做：

```text
create_internal_issue
trigger_diagnostic_workflow
open_dependency_upgrade_pr
```

系统就需要知道：

```text
这个动作是自动执行的？
还是人类批准后执行的？
人类是否修改了风险等级？
人类是否要求更多证据？
```

所以即使 M1 不实现 Human-in-the-loop，也应该先定义这个模型。

---

## 9. 为什么还要有 DependencyMap / Playbook / HistoricalCase？

这三个不是 runtime workflow 的主线模型，而是 support models。

它们回答的是：

```text
系统判断风险时依赖什么上下文？
```

### DependencyMap

告诉系统：

```text
我们的 SaaS 产品依赖哪些外部服务？
这些依赖影响哪个模块？
它们的重要性是什么？
```

例如：

```text
CI/CD Pipeline -> GitHub Actions -> high criticality
Billing -> Stripe API -> critical
AI Assistant -> OpenAI API -> high
```

没有 DependencyMap，系统无法判断某个外部事件是否和自己有关。

---

### Playbook

告诉系统：

```text
遇到某类事件通常怎么处理？
```

例如：

```text
service_incident + high criticality dependency
→ notify_support
→ review_required = true
```

没有 Playbook，recommended_action 就会变成 LLM 随便编。

---

### HistoricalCase

告诉系统：

```text
过去类似事件怎么处理？
结果怎样？
有什么经验？
```

它支持后续 RAG 和 replay evaluation。

---

## 10. 为什么需要 EvalCase？

EvalCase 是为了后续 evaluation。

很多 Agent 项目没有 evaluation，一般只能靠主观感觉：

```text
这个回答好像不错
这个 summary 看起来还行
```

但 EventFlow 要评估的是 workflow 行为：

```text
event_type 是否分类对？
affected_dependencies 是否正确？
risk_level 是否合理？
route 是否正确？
recommended_action 是否合理？
```

所以 EvalCase 需要保存 expected labels：

```text
expected_event_type
expected_affected_dependencies
expected_risk_level
expected_route
expected_recommended_action
```

注意：EvalCase 的 label 不能完全相信 AI 生成。  
AI 可以 draft，但你需要 review。

否则 evaluation 会变成：

> 用 AI 生成标准答案，再用 AI 系统去迎合这个标准答案。

这样价值很低。

---

## 11. 字段设计时应该怎么想？

以后你设计任何 Agent 项目的 data model，可以把字段分成几类。

### Identity fields

用于唯一识别。

```text
signal_id
candidate_id
cluster_id
brief_id
```

### Provenance fields

用于追溯来源。

```text
source_signal_id
source_type
source_url
vendor
evidence_refs
```

### Content fields

用于保存文本内容。

```text
title
content
summary
rationale
guidance
```

### Classification fields

用于表达系统判断。

```text
event_type
risk_level
recommended_action
review_status
```

### Confidence fields

用于表达不确定性。

```text
confidence
retrieval_quality
```

### Routing fields

用于控制 workflow 路由。

```text
requires_human_review
expected_route
review_required
```

### Audit fields

用于记录时间和人类操作。

```text
created_at
reviewed_at
reviewer_id
comments
```

这个分类方法很实用。以后做别的 Agent 项目也可以用。

---

## 12. 为什么 M1 不要把字段设计得太复杂？

初学者很容易犯一个错误：

> 把未来可能会用到的字段全塞进 schema。

比如一开始就加：

```text
tenant_id
workspace_id
permission_policy
remediation_plan
cost_estimate
customer_impact_score
sla_impact
notification_channels
```

这些字段听起来高级，但 M1 用不到。

过早加入太多字段会导致：

```text
实现复杂
测试复杂
样例数据难维护
Codex 更容易乱写
你自己更难解释
```

所以 M1 应该坚持：

> 只加当前 workflow 可以解释清楚的字段。

未来真的进入 V2/V3，再扩展。

---

## 13. Data model 如何帮助测试？

有了 schema，就可以写很多低成本测试。

### Schema validation tests

检查：

```text
缺字段会不会失败？
非法 event_type 会不会失败？
confidence > 1 会不会失败？
空 title 会不会失败？
```

### Node unit tests

每个 node 可以测试输入输出：

```text
RawSignal -> EventCandidate
EventCandidate + EvidencePack -> RiskAssessment
RiskAssessment -> EventRiskBrief
```

### Graph integration tests

后续 LangGraph 可以测试路径：

```text
low risk -> auto brief
high risk -> human review
missing evidence -> request_more_evidence
```

### Eval tests

用 EvalCase 测试：

```text
分类准确率
risk routing 准确率
review trigger recall
unsupported fact rate
```

所以 M1 虽然看起来只是 data model，但它是后面所有测试的基础。

---

## 14. 常见错误

### 错误 1：到处传 dict

短期很快，长期灾难。

问题：

```text
字段名拼错不报错
测试不稳定
Codex 容易乱加字段
后续重构困难
```

---

### 错误 2：Raw input 和 processed result 混在一起

应该保留 raw input，再单独保存 interpretation。

---

### 错误 3：没有 evidence 字段

没有 evidence_refs，后续无法判断模型是否 hallucinate。

---

### 错误 4：没有 confidence

没有 confidence，系统很难决定什么时候需要 human review。

---

### 错误 5：risk 和 final output 混在一起

RiskAssessment 和 EventRiskBrief 职责不同，应分开。

---

### 错误 6：eval labels 全交给 AI

AI 可以生成草稿，但你必须 review gold labels。

---

### 错误 7：schema 太超前

不要为了未来 V3 自动修复，一开始就在 M1 加 remediation fields。

---

## 15. 以后做类似项目时的通用 checklist

当你做一个新的 Agent / RAG / Workflow 项目时，可以按这个 checklist 推导 data model。

### Step 1：确定 workflow

```text
系统输入是什么？
中间有哪些处理步骤？
最终输出是什么？
```

### Step 2：找出每一步的状态

```text
每一步产生什么结果？
下一步需要什么信息？
哪些信息要保留？
```

### Step 3：区分 raw data 和 interpreted data

```text
哪些是原始输入？
哪些是系统理解？
哪些可能出错？
```

### Step 4：设计 evidence

```text
判断依据从哪里来？
需要保存哪些证据引用？
```

### Step 5：设计 confidence 和 routing

```text
什么时候自动处理？
什么时候人审？
什么时候请求更多证据？
```

### Step 6：设计 final output

```text
最终给谁看？
需要包含哪些字段？
哪些字段是内部判断，不应该直接展示？
```

### Step 7：设计 eval data

```text
什么算做对？
gold label 是什么？
如何复现测试？
```

### Step 8：控制范围

```text
哪些字段现在必须有？
哪些字段以后再加？
哪些功能属于 post-MVP？
```

---

## 16. 总结

EventFlow 的 data model 不是为了“看起来完整”，而是为了让 Agent workflow 可控。

核心思想是：

```text
原始输入和系统理解分开
证据和判断分开
内部决策和最终展示分开
workflow runtime model 和 dataset support model 分开
MVP 字段和未来扩展字段分开
```

这套思路不仅适用于 EventFlow，也适用于很多 AI Agent 工程项目。
