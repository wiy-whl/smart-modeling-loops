# Legacy 循环归档说明

本目录下的循环来自原版 [smart-modeling-loops](https://github.com/wiy-whl/smart-modeling-loops)，面向 **ER/数据库建模** 语境（需求解析 → 实体字段 → 验证），与海致智能建模 **NL2Model（自然语言 → 可视化画布）** 产品核心不符。

| 文件 | 原用途 | 归档原因 |
|------|--------|----------|
| 需求解析循环.yaml | 业务需求 → 实体字段摘要 | 非 NL2Model 主链路 |
| 建模方案生成循环.yaml | 生成 ER 建模方案 | 输出对象应为 plan JSON，非 Markdown 方案 |
| 模型验证循环.yaml | ER 模型验证报告 | 评测量规应对齐 Agent 契约 |
| agent链路测试循环.yaml | 初版 Agent 测试 | 已被 `主链路E2E评测循环.yaml` 替代 |
| 产品文档维护循环.yaml | 文档复制归档 | L3 辅助，非产品核心循环 |

**当前活跃循环**见 `loops/主链路E2E评测循环.yaml` 与 `loops/OPT回归循环.yaml`。

产品核心定义：`artifacts/产品定义/产品核心定义.md`
