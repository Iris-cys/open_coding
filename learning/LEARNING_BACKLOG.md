# 待学习列表（Learning Backlog）

> 目的：把分散在对话中的长期学习项目集中管理，避免遗忘。
>
> 最后更新：2026-09-20

## A. 当前主线 / 正在推进

### 1. PCIe
- [ ] PCIe 系统学习：Architecture → Transaction Layer → Data Link Layer → Physical Layer → Verification Practice
- [ ] PCIe Gen6 / FLIT Mode 深入学习
- [ ] PCIe → CHI/NoC → CXL 学习链路
- 目标：具备更强的 PCIe / 体系结构验证能力。

### 2. GPU / GPU Command Processor
- [ ] GPU 基础与宏观体系结构
- [ ] GPU Command Processor（CP）数据流与模块职责
- [ ] CPE / CPF 等模块
- [ ] 并行计算基础
- 目标：支撑当前 GPU CP / Cache / 体系结构验证工作。

### 3. Digital Design and Computer Architecture（RISC-V）
- [ ] 继续《Digital Design and Computer Architecture: RISC-V Edition》
- 主线：数字逻辑 → CPU → Pipeline → Cache → Memory Hierarchy → Virtual Memory → Parallel Computing
- 目标：补齐体系结构底座，并与 PCIe / Cache / NoC 验证连接起来。

## B. AI / AI Engineering

### 4. 吴恩达《AI Prompting for Everyone》
- [ ] 待学习
- 时长：约 8 小时
- 版本：DeepSeek-v4-pro 翻译
- B站：BV1UT9qBDET7
- 原始链接：https://b23.tv/hbSePNm
- 目的：更好地使用 AI，并为未来工作做准备。
- 优先级：有时间学习，非紧急。

### 5. Microsoft《AI Agents for Beginners》
- [ ] 待学习
- 约 10 节课，从 Agent 原理到可运行代码。
- 目的：建立 AI Agent 的系统认知与实践能力。

### 6. AI Agent / MCP / AI Workflow
- [ ] AI Agent
- [ ] MCP
- [ ] AI Workflow / 自动化
- [ ] IC Agent / AI for EDA
- 目标：理解 AI 如何真正进入芯片设计与验证工作流。

## C. AI Infra

### 7. AI Infra 系统学习
- [ ] AI workload 数据流：Weight / Activation / Gradient / Optimizer State
- [ ] 多 GPU 并行：Data / Tensor / Pipeline / Expert Parallel
- [ ] Collective Communication：AllReduce / AllGather / ReduceScatter 等
- [ ] GPU / HBM / PCIe / NIC 数据路径
- [ ] RDMA / InfiniBand / RoCE
- [ ] NVLink / NVSwitch
- [ ] CUDA / NCCL
- [ ] Scheduler / Serving / AI Runtime
- 目标：从芯片验证视角建立“芯片 → 互连 → 内存 → 集群 → 软件”的完整系统认知。

## D. 高速互连

### 8. CHI / NoC
- [ ] CHI 系统学习
- [ ] NoC 与一致性
- 目标：PCIe 之后继续向片上互连和体系结构验证扩展。

### 9. CXL
- [ ] CXL 系统学习
- 建议顺序：PCIe → CHI/NoC → CXL
- 目标：理解下一代内存/设备互连体系。

### 10. SerDes / 高速互连
- [ ] SerDes 基础
- [ ] Ethernet / FEC
- [ ] AI 高速互连
- 目标：补齐 PCIe Physical Layer 与 AI Infra 高速通信底层知识。

## E. 计算机系统基础

### 11. 操作系统
- [ ] OS 基础

### 12. 计算机网络
- [ ] 网络基础

### 13. 虚拟化
- [ ] Virtualization 基础

这些内容不是独立知识点，而是为 PCIe、CXL、GPU、AI Infra 和体系结构验证提供系统软件背景。

---

## 使用规则

- **主线优先**：PCIe / GPU / 体系结构。
- **AI 长期线**：Prompt → Agent → MCP / Workflow → AI for EDA。
- **系统扩展线**：AI Infra → CHI/NoC → CXL → 高速互连。
- 新出现“以后想学”的课程、书籍或技术主题，统一追加到本文件。
- 学完后不要直接删除：将 `[ ]` 改成 `[x]`，保留学习轨迹。
