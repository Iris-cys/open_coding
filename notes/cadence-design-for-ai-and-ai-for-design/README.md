# Cadence《Design for AI and AI for Design》：关键观点与认知转变

> 演讲者：Charles Alpert，Cadence AI Fellow  
> 主题：用 EDA 设计 AI 基础设施，以及用 AI 重构芯片设计流程  
> 整理日期：2026-09-16

## 一句话结论

这场演讲真正重要的，不是“AI 能帮工程师写 RTL、写 test 或 Debug”，而是：

> **EDA 正从“人操作一组工具”，重构为“Agent 围绕设计意图，调度可信工程引擎并持续闭环”。**

这与 Spec → feature list → test point → verification → debug 的 Agent 化高度相关。

## 1. 总框架：两个方向、一个飞轮

### Design for AI

用芯片设计、EDA、仿真、封装、散热和系统设计技术，构建 AI 基础设施。

### AI for Design

用 AI 反过来改造芯片、系统和工程流程的设计方法。

二者组成持续增强的飞轮：

```text
更好的 AI 芯片 → 更强的 AI → 更强的 EDA Agent → 更快设计下一代 AI 芯片
```

## 2. 八个 Key Points

### 2.1 新瓶颈：从晶体管密度转向工程师生产力

AI 芯片的设计对象已不只是单颗芯片，而是 chiplet、3D IC、HBM、高速互连、功耗、热、软件与 workload 的联合系统。设计空间大到人无法手工穷举。

**认知转变：** AI 的首要价值不是“省几个人”，而是突破人类可处理的工程复杂度上限。有些问题没有 AI 并不只是晚两个月，而是可能根本无法有效探索。

### 2.2 AI for EDA 的终局不是 Copilot，而是 Agent

能力演进可以理解为：

```text
Optimization AI → Conversational LLM → Reasoning → Agentic Workflow → Autonomy
```

Copilot 是“帮我写一个 assertion”；Agent 则会理解目标、制定计划、调用工具、读取结果、修正方案并迭代到目标达成。

```text
AI → Action → Result → Reasoning → Action → Result
```

### 2.3 LLM 不是判定真假的核心，工程 Solver 才是

Agent 负责 reasoning、planning 和 orchestration；真正判定设计是否正确的，仍是 simulator、formal solver、STA、lint、CDC、DRC、LVS、功耗与热仿真等可信工程引擎。

```text
                  AI Agent
           Reason / Plan / Orchestrate
                       │
       ┌───────────────┼───────────────┐
       ↓               ↓               ↓
      Spec            RTL             Tests
       └───────────────┼───────────────┘
                       ↓
       Simulation / Formal / Lint / CDC / STA
                       ↓
                    Evidence
                       ↓
                 Agent 再判断与行动
```

**关键问题应从**“如何让 AI 不产生幻觉”**改为**“如何让 AI 的每个关键结论都必须通过可执行的工程 oracle”。

### 2.4 未来 EDA 的基本单位不是 Tool，而是 Workflow

传统视角是 Xcelium、Jasper、Verdi、Genus、Innovus、Tempus 等工具列表；Agent 的视角则是：

```text
Goal → Workflow → Evidence → Decision
```

例如目标不是“运行 Jasper”，而是“证明 DPC 触发后 downstream traffic 被正确 containment”。Agent 再自行决定读取哪些 Spec/RTL、生成哪些 property、调用什么引擎以及如何分析反例。

EDA 的入口将从 **Tool-Centric** 转向 **Intent-Centric**。

### 2.5 稀缺能力转向定义 Design Intent

当 Agent 越来越擅长写代码、跑工具、搜索参数和 Debug，工程师的价值会从 How 上移到 What + Why。

对验证工程师而言，核心不再只是写 sequence、scoreboard、assertion，而是定义：

- 系统必须满足什么性质；
- 什么状态绝不允许发生；
- 什么证据足以证明需求已覆盖；
- 错误检测、隔离、记录、通知和恢复之间应满足什么 invariant。

验证工程师将从 testcase writer 迁移为 verification architect。

### 2.6 工程 Agent 必须能长时间、有状态地运行

芯片设计不是 Prompt → Answer，而是持续数小时甚至数天的执行循环：仿真、分析、formal、反例、修改约束、回归、覆盖率缺口、补测试、再运行。

因此 Agent 必须具备：状态、记忆、恢复、执行、等待和迭代能力。普通 Chatbot 并不等于 Engineering Agent。

### 2.7 算力不仅训练 AI，也会反过来加速 EDA

GPU 和专用硬件会直接加速工程仿真、求解和多物理场分析，从而形成第二个飞轮：

```text
GPU → 加速 EDA → 更快设计 GPU → 更强 GPU → 更快 EDA
```

未来 AI、HPC 与 EDA 会越来越难分开。

### 2.8 设计边界从 Silicon 扩展到 System

优化对象正在扩展：

```text
Transistor → Chip → Chiplet → Package → Board → Rack → Cooling → Data Center → Workload
```

这要求从单点优化转向 System Technology Co-Optimization / Cross-Technology Co-Optimization。

## 3. 对验证 Agent 的直接启示

Spec 自动生成 verification plan 只是第一步。真正的闭环应是：

```text
Spec / RTL / Interface
          ↓
  Requirement Graph
          ↓
    Feature Model
          ↓
 Verification Model
  ├─ stimulus
  ├─ checker
  └─ coverage
          ↓
 Sim / Formal / Lint
          ↓
     Evidence DB
          ↓
 Reasoning Agent
  ├─ gap finding
  ├─ debug
  └─ iteration
```

真正有价值的不是单次生成 testplan.md，而是建立以下结构化层：

| 层次 | 作用 |
|---|---|
| Requirement Graph | 保存需求、来源、依赖、冲突与追踪关系 |
| Feature Model | 用维度和组合描述功能空间 |
| Verification Model | 将需求映射到 stimulus、checker、coverage |
| Evidence DB | 保存每项结论的仿真、formal、日志和覆盖证据 |
| Oracle | 用可执行引擎判断对错，而非依赖语言模型自证 |

因此，产品不应只叫 **AI Testplan Generator**，更准确的定位是 **Verification Reasoning System**。

## 4. 最值得带走的五个认知

1. **AI 的价值不是简单替人写代码，而是扩大人类可处理的工程设计空间。**
2. **未来 EDA 的主入口会从 Tool 转向 Intent。** 人告诉 Agent 要证明什么，而不是只告诉它运行什么命令。
3. **LLM 不应成为真理源。** Simulator、Formal、Compiler 和 Spec checker 才是 oracle。
4. **验证工程师会从 testcase writer 向 verification architect 迁移。** 核心能力是 requirement、invariant、coverage model 和 oracle。
5. **AI Agent 的核心不是生成，而是闭环。**

> **Generation is cheap. Verification is the moat.**

## 5. 对个人能力建设的映射

接下来应重点训练四种能力：

- **设计意图建模：** 将自然语言需求转化为 requirement、约束和 invariant。
- **验证空间划分：** 用正交维度、状态机、因果链和组合覆盖描述完备性。
- **证据链设计：** 每个结论都能追溯到 Spec、RTL、接口、测试与工具结果。
- **闭环架构：** 让 Agent 能运行工具、读取反馈、定位缺口并继续迭代，而不只是生成文档。

最终应把问题从：

> “AI 能不能帮我写验证？”

升级为：

> **“怎样把验证工程变成一个可由 Agent 自主规划、执行、获得证据、发现缺口并持续闭环的系统？”**

## 6. 参考资料

- [AI Infra Summit 官方回放页](https://www.ai-infra-summit.com/keynote-recordings/design-ai-ai-design-charles-alpert-ai-fellow-cadence)
- [Cadence 官方视频页](https://www.cadence.com/en_US/home/resources/videos/tools/ai/design-for-ai-and-ai-for-design.html)
- [Cadence：Powering the AI Supercycle](https://community.cadence.com/cadence_blogs_8/b/corporate-news/posts/powering-the-ai-supercycle-design-for-ai-and-ai-for-design)
- [AI Infra Summit Hardware & Systems Insights Report](https://cdn.asp.events/CLIENT_Kisaco_R_E0D4AD69_B740_B124_D2ADF5A777880773/sites/AI-Infra-Summit-2026/media/libraries/downloads/Hardware-and-Systems-Insights-Reports.pdf)
- [Cadence 与 NVIDIA 加速工程解决方案](https://www.cadence.com/en_US/home/company/newsroom/press-releases/pr/2026/cadence-and-nvidia-unveil-accelerated-engineering-solutions.html)

> 注：官方 2026 站点提供该回放，但部分大会总结材料与 Cadence 页面存在 2025/2026 归档口径混用。引用具体年份时应再次核对原始页面。
