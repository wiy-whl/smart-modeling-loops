# 变更日志

## 2026-07-28

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
