# Smart Modeling Core 与 Product Loops 关系

## 2026-07-28 决策

采用 **loop-engineering-core → smart-modeling-core → smart-modeling-loops** 三层架构：

1. 通用方法论不重复造轮子，继承 loop-engineering-core
2. 智能建模领域知识（Agent、JSON、评测）沉淀在 smart-modeling-core
3. 海致具体产物（白皮书、测试、OPT）放在 smart-modeling-loops

## 理由

- 与海致 Wiki 技术方案、测试反馈直接对齐
- Agent JSON 传参规范可独立演进
- 产品库可单独发布，不污染通用核心库
