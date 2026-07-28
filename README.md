# 智能建模产品库（Smart Modeling Loops）

> 基于 [smart-modeling-core](../smart-modeling-core) 与 [loop-engineering-core](https://github.com/wiy-whl/loop-engineering-core) 构建的海致智能建模产品库。

## 这是什么

本产品库管理海致**智能建模助手**从需求、文档、测试到 Agent 验证的完整 PM 工作循环，并与内部 Wiki 技术方案、测试反馈、产品文档对齐。

## 核心库继承

```
loop-engineering-core v1.0.0        ← 通用循环工程方法论
        ↓
smart-modeling-core v1.0.0          ← 智能建模领域扩展（Agent/JSON/评测）
        ↓
smart-modeling-loops（本库）         ← 海致智能建模具体产物与循环
```

## 循环流水线

```
inputs/raw/（测试用例、文档需求）
    │
    ├─→ [agent链路测试循环] ──→ artifacts/测试报告/
    ├─→ [产品文档维护循环] ──→ artifacts/产品文档/
    ├─→ [需求解析循环]       ──→ artifacts/建模方案/需求摘要.md
    ├─→ [建模方案生成循环]   ──→ artifacts/建模方案/建模方案.md
    └─→ [模型验证循环]       ──→ artifacts/验证报告/验证报告.md
```

## 产品库结构

```
smart-modeling-loops/
├── .core-version                    # smart-modeling-core@1.0.0
├── CLAUDE.md
├── loops/                           # 5 个循环定义
├── artifacts/
│   ├── 产品文档/                    # 白皮书、操作手册
│   ├── 测试报告/                    # 优化记录、测试报告
│   ├── Agent契约/                   # JSON Schema
│   └── 建模方案/                    # 建模方案模板与产出
├── inputs/raw/                      # 测试用例、文档需求
├── inputs/config/                   # Agent JSON 协议配置
├── eval-data/rubrics/               # 评测量规
├── docs/guides/                     # Agent 架构解读等
└── runs/                            # 运行锁定与历史
```

## 已纳入的产物

| 产物 | 路径 |
|------|------|
| 产品白皮书 | `artifacts/产品文档/产品白皮书.md` |
| 智能建模操作手册 | `artifacts/产品文档/操作手册-智能建模助手.md` |
| Data Agent 操作手册 | `artifacts/产品文档/操作手册-DataAgent.md` |
| 产品优化记录 OPT-001~012 | `artifacts/测试报告/产品优化记录.md` |
| Agent JSON Schema | `artifacts/Agent契约/` |
| 0723 测试基线 | `eval-data/baselines/智能建模评测-0723.txt` |

## Agent 主链路

```
RecognitionAgent → NL2ModelDesignAgent → NL2TableOperatorAgent → NL2OperatorAgent → 画布
```

详见 `docs/guides/Agent架构解读.md` 与核心库 `框架/Agent架构规范.md`。

## 快速开始

1. 阅读 `../smart-modeling-core/README.md` 了解领域核心库
2. 将测试用例放入 `inputs/raw/`
3. 触发 `loops/agent链路测试循环.yaml`
4. 对照 `eval-data/rubrics/智能建模评测量规.yaml` 查看评分
5. 在 `artifacts/测试报告/` 查看输出

## 与原版 smart-modeling-loops 的差异

本仓库在 [wiy-whl/smart-modeling-loops](https://github.com/wiy-whl/smart-modeling-loops) 基础上完善：

- 新增 `smart-modeling-core` 领域核心库引用
- 纳入海致真实测试用例与 OPT 优化项
- 新增 Agent 链路测试、产品文档维护循环
- 纳入白皮书、操作手册、优化记录等产物
- 定义三 Agent JSON Schema 契约

## 许可

MIT License
