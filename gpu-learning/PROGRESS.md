# GPU Learning Progress

Updated: 2026-09-18

## Goal
建立 GPU 第一性原理知识体系，不以背名词为目标。最终能把概念讲给零基础的人并让对方理解，并通过教授式深度口试。

## Textbook
Programming Massively Parallel Processors: A Hands-on Approach, Fifth Edition (Hwu / Kirk / El Hajj)

主线：Chapter 1 → Chapter 2 → Chapter 4 → Chapter 5。

## Learning protocol
1. 先问需要改变什么认知，而不是先背定义。
2. 从工程问题、目标、约束出发做第一性原理推导。
3. 再映射到正式术语、硬件结构与教材。
4. Mastery L1：能给零基础者讲懂。
5. Mastery L2：能从因果和约束自行推导机制。
6. Mastery L3：能处理反例、边界条件、跨概念连接与工程迁移。
7. 每课由“老教授式口试”验收，不只考名词定义。

## Current progress
- [x] Lesson 01: 为什么需要 GPU / 为什么计算走向并行
- [ ] Lesson 02: Latency vs Throughput —— CPU/GPU 优化目标
- [ ] Lesson 03: Thread 的本质
- [ ] Lesson 04: Warp 与 SIMD/SIMT
- [ ] Lesson 05: SM 与执行单元
- [ ] Lesson 06: Warp scheduling 与 latency hiding
- [ ] Lesson 07: GPU memory hierarchy

## Lesson 01 key cognitive change
“CPU=串行、GPU=并行”是错误模型。CPU 同样利用并行。下一步真正要解释的是：CPU 和 GPU 都能并行，为什么采用不同的资源组织和优化目标？

## Resume instruction for a new chat
先读取本文件。不要重新从 GPU 名词表开始。根据最后一个已完成 Lesson 继续；讲授顺序必须是：认知改变 → 第一性问题 → 原理推导 → 正式术语 → 工程连接 → 教授式口试 → 更新本文件。
