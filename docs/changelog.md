# 变更日志

## 2026-07-28 — Phase 1 产品核心重构

### 锚定 NL2Model 产品核心

- 新增 `artifacts/产品定义/产品核心定义.md` — 所有循环的唯一锚点
- 明确四条能力环 C1–C4，区分智能建模 vs ER 建模 vs Data Agent
- 重写 README、CLAUDE.md，主循环从 ER 建模转向 E2E 评测

### 主链路 E2E 评测体系

- 0723 测试用例 → `inputs/scenarios/SCN-001~005.yaml` + `expected/`
- 新增 `loops/主链路E2E评测循环.yaml`、`loops/OPT回归循环.yaml`
- 新增 `eval-data/rubrics/主链路评测量规.yaml`（六维度对齐能力环）
- 新增 `artifacts/优化追踪/OPT-registry.yaml`（OPT ↔ scenario 映射）
- 新增 `scripts/run_e2e_eval.py` 半自动评测脚本

### Legacy 归档

- 旧循环移至 `loops/legacy/`：需求解析、建模方案生成、模型验证、agent链路测试、产品文档维护

---

## 2026-07-28 — 产品文档维护循环（L3）

### 产品文档维护循环 — 首次运行

- 运行 ID: `2026-07-28_10-59-15`
- 输入: 10 份源文档（白皮书、操作手册、优化记录、介绍文档等）
- 输出: `artifacts/产品文档/*_v*.md`（含产物元数据 frontmatter）
- 评分: rubric_aggregate 0.95，状态待人工评审
- 运行记录: `runs/history/2026-07-28_10-59-15/`

### 完善（本地工作区）

- 新建 `smart-modeling-core` 领域核心库
- 完善本产品库目录结构（inputs/eval/runs/docs）
- 新增循环：`agent链路测试循环`、`产品文档维护循环`
- 新增脚本：`scripts/run_product_doc_loop.py`
- 纳入产物：白皮书、操作手册、优化记录、Agent Schema
- 新增测试用例 `inputs/raw/智能建模测试用例-0723.md`
- 更新 `.core-version` 指向 smart-modeling-core@1.0.0
- 更新 README、CLAUDE.md

## 初始版本

- 来源：[wiy-whl/smart-modeling-loops](https://github.com/wiy-whl/smart-modeling-loops)
- 含需求解析、建模方案生成、模型验证三个循环
