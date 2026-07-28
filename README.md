# 智能建模产品库（Smart Modeling Loops）

> 基于 [loop-engineering-core](https://github.com/wiy-whl/loop-engineering-core) 构建的海致**智能建模助手** PM 循环工程产品库。

## 产品核心

**用户用自然语言描述需求 → 系统产出可运行、可验证、可迭代的可视化模型。**

这不是 ER/数据库建模工具，而是 NL2Model 多 Agent 编排产品。所有循环与评测围绕四条能力环：

| 能力环 | Agent / 环节 | 验收点 |
|--------|-------------|--------|
| C1 意图理解 | RecognitionAgent | 正确路由到建模链路 |
| C2 选表规划 | NL2ModelDesign + NL2TableOperator | plan JSON + 选对表 |
| C3 算子落地 | NL2OperatorAgent → 画布 | 合规 params，模型可运行 |
| C4 体验可信 | 前端交互 | 流式稳定、会话可追溯 |

详见 `artifacts/产品定义/产品核心定义.md`。

## 架构

```
loop-engineering-core v1.0.0        ← 通用循环工程方法论
        ↓
smart-modeling-loops（本库）         ← 海致智能建模产物、场景、评测、OPT
```

## 主循环（L1）

```
inputs/scenarios/*.yaml          ← 0723 测试用例结构化
        ↓
[主链路E2E评测循环]              ← scripts/run_e2e_eval.py
        ↓
artifacts/评测基线/reports/       ← E2E 评测报告
artifacts/优化追踪/OPT-registry  ← OPT ↔ scenario 闭环
        ↓
[OPT回归循环]                    ← 修复后仅跑关联 scenario
```

## 产品库结构

```
smart-modeling-loops/
├── artifacts/
│   ├── 产品定义/                  # 产品核心定义（所有循环的锚点）
│   ├── 优化追踪/                  # OPT-registry.yaml
│   ├── 评测基线/                  # scenarios / expected / reports
│   ├── Agent契约/                 # JSON Schema
│   └── 产品文档/                  # 白皮书、操作手册（L3 辅助）
├── inputs/
│   ├── scenarios/                 # E2E 测试场景 + expected/
│   ├── feedback/                  # PM 手工观测
│   └── docs/                      # 参考文档（非主循环输入）
├── loops/
│   ├── 主链路E2E评测循环.yaml     # 主循环
│   ├── OPT回归循环.yaml
│   └── legacy/                    # 旧 ER 建模循环（已归档）
├── eval-data/rubrics/
│   └── 主链路评测量规.yaml
├── scripts/
│   └── run_e2e_eval.py            # 半自动评测脚本
└── runs/                          # run-lock 与运行历史
```

## 快速开始

```bash
# 1. 查看全部测试场景
python scripts/run_e2e_eval.py --list

# 2. 用 0723 baseline 跑首次 E2E 评测
python scripts/run_e2e_eval.py

# 3. 查看报告
# artifacts/评测基线/reports/E2E评测报告_*.md

# 4. 修复后回归单个 OPT
python scripts/run_e2e_eval.py --opt OPT-003
```

## 当前 P0 状态（0723 baseline）

| OPT | 场景 | 问题 |
|-----|------|------|
| OPT-001/002 | SCN-005 | 手动选表后仍推荐、无规划 |
| OPT-003 | SCN-001 | 算子参数生成失败 |
| OPT-006 | SCN-003 | 多表只能二选一 |

## Agent 主链路

```
RecognitionAgent → NL2ModelDesignAgent → NL2TableOperatorAgent → NL2OperatorAgent → 画布
```

Schema：`artifacts/Agent契约/` · 架构解读：`docs/guides/Agent架构解读.md`

## 与旧版差异

| 维度 | 旧版 | 现版 |
|------|------|------|
| 产品核心 | ER 建模（实体/字段） | NL2Model（自然语言→画布） |
| 主循环 | 需求解析→方案→验证 | 主链路 E2E 评测 + OPT 回归 |
| 评测输入 | 自由文本需求 | 结构化 scenario + expected |
| 文档循环 | 无 | L3 辅助，非主循环 |

## 许可

MIT License
