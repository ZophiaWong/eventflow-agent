# EventFlow Design Rationale

这是一份学习和面试复盘文档，用来解释 EventFlow Agent 为什么这样设计。

它不是架构契约。真正的系统架构说明在：

```text
docs/architecture/architecture-overview.md
```

这份文档回答的问题是：

> 为什么 EventFlow 不是一个普通 summary bot？
> 为什么它要设计成 external event triage workflow？
> 为什么要先做 Event Risk Brief，再考虑 tool calling？
> 为什么要用 LangGraph？
> 为什么要有 Human-in-the-loop？
> 为什么用 synthetic data 也有价值？

---

## 1. 这个项目到底在解决什么问题？

EventFlow Agent 解决的不是“帮我总结新闻”。

它模拟的是一个 SaaS 团队处理外部事件的流程。

现代 SaaS 产品通常依赖很多外部服务：

```text
GitHub Actions
Stripe API
OpenAI API
AWS S3
Vercel
PostgreSQL
FastAPI
Pydantic
LangGraph
SendGrid
```

这些外部依赖会不断产生事件：

```text
服务故障
安全公告
API breaking change
SDK release
产品更新
deprecation notice
```

问题是：这些事件不一定都重要。

同样一条事件，对不同团队影响不同。

例如：

```text
GitHub Actions 出现 job start delay
```

对一个不依赖 GitHub Actions 的团队可能无所谓。  
但对一个所有部署流程都依赖 GitHub Actions 的 SaaS 团队，可能意味着：

```text
CI/CD 延迟
hotfix 发布受阻
测试队列变慢
支持团队需要解释交付延迟
```

所以真正的问题不是：

> 发生了什么？

而是：

```text
这件事和我们有关吗？
影响哪个 dependency？
风险多高？
需要通知谁？
需要人类审核吗？
下一步动作是什么？
```

EventFlow 的目标就是把这些问题变成一个可执行、可测试、可复盘的 workflow。

---

## 2. 为什么不是普通新闻总结器？

普通总结器做的是：

```text
输入一段文字
输出一段摘要
```

EventFlow 做的是：

```text
输入外部事件信号
识别事件类型
匹配内部依赖
检索 playbook / historical cases
判断风险等级
决定是否需要人审
生成结构化 brief
未来触发受控 tool action
```

区别在于：

| 普通总结器          | EventFlow Agent              |
| ------------------- | ---------------------------- |
| 关注文本摘要        | 关注事件 triage              |
| 输出自然语言        | 输出结构化 Event Risk Brief  |
| 不关心依赖关系      | 显式匹配 dependency map      |
| 不关心风险路由      | 有 risk level / review route |
| 不关心证据          | 有 evidence_refs             |
| 不关心人审          | 有 Human-in-the-loop         |
| 不适合评估 workflow | 可以做 replay evaluation     |

所以 EventFlow 不是为了“把信息说得更短”，而是为了：

> 把外部信号转化成团队可以行动的结构化判断。

---

## 3. 为什么设计成 external event triage workflow？

`triage` 的意思是分诊、分流。

在 EventFlow 中，triage 解决的是：

```text
哪些事件可以忽略？
哪些事件只需要观察？
哪些事件需要通知支持团队？
哪些事件需要创建内部 issue？
哪些事件需要升级给工程团队？
哪些事件需要更多证据？
哪些事件必须人审？
```

这个设计比“总结所有事件”更贴近真实工作流。

因为企业中真正消耗精力的往往不是读消息，而是判断：

```text
要不要处理？
谁处理？
多紧急？
有没有依据？
后续如何复盘？
```

所以 EventFlow 的核心不是：

```text
summarization
```

而是：

```text
classification
dependency impact analysis
evidence retrieval
risk routing
human review
action recommendation
evaluation
```

---

## 4. 为什么选择 SaaS external events 这个场景？

选择这个场景有几个原因。

### 4.1 场景足够真实

SaaS 产品确实依赖大量外部服务和开源组件。

这些外部依赖的事件会影响：

```text
发布流程
客户体验
安全响应
支持团队话术
内部工程优先级
```

---

### 4.2 场景适合 portfolio project

真实企业内部数据很难获得，也不适合公开。

但 external SaaS event 场景可以用：

```text
公开 vendor/dependency 名称
合成事件内容
模拟 dependency map
模拟 playbook
模拟 historical cases
```

这样项目可以公开展示，又不需要伪造真实业务。

---

### 4.3 场景能覆盖 AI Agent 工程能力

这个场景自然包含：

```text
LangGraph workflow
RAG / evidence retrieval
structured state
conditional routing
Human-in-the-loop
tool calling boundary
evaluation
```

这些都和 AI Agent 工程师岗位高度相关。

---

### 4.4 场景不会一开始太大

相比金融风控、舆情分析、市场情报，SaaS external events 更容易控制范围。

MVP 只需要四类事件：

```text
service_incident
security_advisory
api_change
product_release
```

这对 junior developer 更适合。

---

## 5. 为什么采用 RawSignal → EventRiskBrief 这种流程？

这个流程是从“原始信息”到“可行动判断”的逐步加工。

```text
RawSignal
→ EventCandidate
→ EventCluster
→ EvidencePack
→ RiskAssessment
→ HumanReviewDecision
→ EventRiskBrief
```

每一步都有明确职责。

### RawSignal

保存原始输入，避免一开始丢信息。

### EventCandidate

保存系统初步理解，但承认它可能错。

### EventCluster

处理重复和相关事件。

### EvidencePack

保存检索到的依赖、playbook、historical cases。

### RiskAssessment

做内部风险判断和路由决策。

### HumanReviewDecision

保存人类审核结果。

### EventRiskBrief

生成最终给人看的结构化结果。

这个流程的好处是：

```text
每一步可测试
每一步可替换
每一步可解释
每一步可以进入 LangGraph state
后续可以做 replay evaluation
```

---

## 6. 为什么先做 Event Risk Brief，而不是直接 Tool Calling？

这是安全和工程成熟度问题。

如果一开始就让 Agent 执行动作，比如：

```text
create issue
send notification
open PR
trigger workflow
rollback
patch dependency
```

项目会立刻变复杂：

```text
权限怎么控制？
动作失败怎么办？
谁审批？
怎么回滚？
怎么避免误操作？
怎么审计？
```

所以更合理的演进是：

```text
MVP: Event Risk Brief
V1: Action Recommendation
V2: Tool Calling with Approval
V3: Controlled Remediation
```

Event Risk Brief 是未来 tool calling 的输入。

它提供：

```text
事件类型
影响依赖
风险等级
证据
推荐动作
review status
```

有了这些结构化信息，后续 action layer 才能安全地判断：

```text
是否允许执行？
是否需要审批？
应该调用哪个 tool？
执行后如何记录？
```

所以 brief 不是最终愿景，而是安全 action orchestration 的基础。

---

## 7. 为什么需要 LangGraph？

如果只是：

```text
输入一段文本
输出一个 brief
```

那不一定需要 LangGraph。

但 EventFlow 不是一条简单 chain。

它需要：

```text
多个节点
共享 state
条件路由
低风险自动通过
高风险进入人审
证据不足时请求更多证据
未来可能 pause / resume
后续可以 replay evaluation
```

这正是 LangGraph 适合的地方。

EventFlow 中 LangGraph 的价值是：

```text
把开放式 Agent 任务变成显式状态机
```

而不是“为了用 LangGraph 而用 LangGraph”。

---

## 8. 为什么需要 Human-in-the-loop？

因为风险判断和 tool action 都可能出错。

高风险事件不应该完全自动化。

例如：

```text
security_advisory 影响核心 dependency
API breaking change 可能影响生产系统
服务故障可能影响客户体验
证据不足但风险可能很高
```

这些场景需要人类确认。

Human-in-the-loop 的作用是：

```text
让系统可以先判断，但不要越权执行
让 reviewer 可以 approve / reject / edit
让决策过程可审计
让未来 tool calling 更安全
```

这也是生产级 Agent 系统的重要思路：

> AI 可以辅助判断和准备动作，但高风险动作要有控制边界。

---

## 9. 为什么 MVP 先 offline-first，而不是实时抓取？

很多人一开始会想做：

```text
实时抓 RSS
实时抓 status page
实时接 GitHub API
实时告警
```

但这会引入很多额外复杂度：

```text
API rate limit
网络错误
数据清洗
认证
调度
去重
存储
失败重试
```

这些不是 MVP 的核心。

MVP 真正要验证的是：

```text
事件进入后，workflow 能不能正确处理？
schema 是否稳定？
风险路由是否清楚？
brief 是否结构化？
人审是否能接入？
evaluation 是否能跑？
```

所以先 offline-first：

```text
sample data
本地 JSONL
可重复测试
可稳定 evaluation
```

这样更适合学习和求职展示。

后续如果需要，再增加真实数据源 adapter。

---

## 10. 为什么先做 rule-based baseline，再做 LLM / RAG？

如果一开始就上 LLM，很容易变成：

```text
prompt 写得好像不错
输出看起来还行
但不知道系统到底靠什么判断
```

rule-based baseline 的作用是建立一个确定性参考：

```text
已知输入
确定规则
确定输出
可测试
可比较
```

然后后续再加入：

```text
LLM extraction
RAG evidence retrieval
retrieval quality evaluator
risk rationale generation
```

这样你能说明：

```text
baseline 能做到什么
LLM / RAG 改进了什么
哪些地方仍然需要 rule / human review
```

这比“全靠 LLM”更像工程项目。

---

## 11. 为什么使用 synthetic data？

因为这是公开 portfolio 项目，不应该使用真实企业数据。

synthetic data 的好处：

```text
可公开
可复现
可控
可覆盖边界场景
不会泄露隐私
不会伪造真实业务
```

但 synthetic data 必须诚实标记。

所以项目采用：

```text
公开 vendor/dependency 名称 + 完全合成事件内容
```

例如：

```text
可以用 GitHub Actions 作为 dependency 名称
但事件内容必须是 simulated
不能使用真实 incident ID
不能使用真实 status page URL
不能声称真实发生过
```

这样既有现实感，又不造假。

---

## 12. 这个项目如何体现 AI Agent 工程能力？

EventFlow 能体现的不是“会调 LLM API”，而是更完整的 Agent 工程能力。

包括：

```text
场景建模
workflow design
schema-first state design
LangGraph orchestration
structured node input/output
conditional routing
RAG / evidence retrieval
risk-aware decision making
Human-in-the-loop
evaluation
tool calling safety boundary
documentation and project communication
```

这些能力更接近 AI Agent 工程师岗位需求。

---

## 13. 面试时如何解释项目意义？

可以这样说：

> EventFlow Agent 不是一个新闻总结器，而是一个模拟 SaaS 团队处理外部事件的 Agentic Workflow。它把分散的外部信号，比如 service incident、security advisory、API change、product release，转化为结构化的 Event Risk Brief。系统会结合 dependency map、playbook 和 historical cases 判断这个事件是否影响产品、风险多高、是否需要人审，以及下一步建议动作是什么。

如果面试官质疑：

> 只是生成 brief，价值不大吧？

可以回答：

> 我同意如果只是 summary，价值不大。所以这个项目把 brief 定义成结构化 workflow output，而不是普通摘要。它包含 event type、affected dependencies、evidence_refs、risk_level、recommended_action 和 review_status。后续 V1/V2 会基于这个结构化结果做 action recommendation 和 controlled tool calling。所以 brief 是 action orchestration 的基础。

如果面试官问：

> 为什么不用现成监控工具？

可以回答：

> 现成监控工具更擅长监控系统内部指标和告警。EventFlow 关注的是外部公开信号进入团队后的 triage：这个信号是否和我们有关、影响哪个依赖、风险多高、该不该人审、下一步做什么。它不是替代 Datadog / PagerDuty / Dependabot，而是模拟外部事件到内部决策之间的 Agentic Workflow。

如果面试官问：

> 为什么用 synthetic data？

可以回答：

> 这是 portfolio 项目，没有真实企业数据。我使用公开 vendor/dependency 名称和 synthetic 事件内容，保证项目可公开、可复现、不会伪造真实业务。关键是数据内部自洽：raw signals、dependency map、playbooks、historical cases 和 eval labels 能支撑 workflow、测试和 evaluation。

---

## 14. 这个项目的边界是什么？

MVP 不做：

```text
真实 API 接入
实时监控
真实告警
真实 Slack/Jira/GitHub 写操作
自动修复
复杂 UI
生产权限系统
```

MVP 聚焦：

```text
schema
sample data
baseline workflow
LangGraph workflow
evidence retrieval
human review
event risk brief
evaluation
```

这个边界很重要。

因为 junior 项目最容易犯的错误是范围太大。

EventFlow 的设计原则是：

> 先把 workflow 做清楚，再逐步增强能力。

---

## 15. 总结

EventFlow 这样设计的核心逻辑是：

```text
不是 chatbot，而是 workflow
不是 summary，而是 triage
不是直接 action，而是先 brief / review / policy
不是全靠 LLM，而是 rule + schema + evidence + human review
不是伪造真实业务，而是 synthetic but consistent dataset
```

这个项目真正要展示的是：

> 如何把一个开放式的信息处理问题，拆成一个可控、可测试、可审计、可扩展的 AI Agent workflow。
