#!/usr/bin/env python3
"""主链路 E2E 评测脚本 — 半自动评分与报告生成。

用法:
  python scripts/run_e2e_eval.py                    # 使用 scenario 内嵌 baseline 评分
  python scripts/run_e2e_eval.py --observation path # 使用 PM 手工观测文件
  python scripts/run_e2e_eval.py --list             # 列出全部 scenario
  python scripts/run_e2e_eval.py --opt OPT-003      # 仅跑关联 scenario（回归模式）
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "inputs" / "scenarios"
RUBRIC = ROOT / "eval-data" / "rubrics" / "主链路评测量规.yaml"
OPT_REGISTRY = ROOT / "artifacts" / "优化追踪" / "OPT-registry.yaml"
REPORTS = ROOT / "artifacts" / "评测基线" / "reports"
RUNS = ROOT / "runs" / "history"
MEMORY = ROOT / "memory" / "changelog"


def load_yaml(path: Path) -> Any:
    if yaml is None:
        raise SystemExit("需要 PyYAML: pip install pyyaml")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def list_scenarios() -> list[Path]:
    return sorted(SCENARIOS.glob("SCN-*.yaml"))


def load_rubric() -> dict:
    return load_yaml(RUBRIC)


def normalize_score(raw: float) -> float:
    """0-10 → 0-1"""
    return round(raw / 10.0, 3)


def weighted_aggregate(scores: dict[str, float], rubric: dict) -> float:
    total_w = 0.0
    total = 0.0
    for dim in rubric["dimensions"]:
        dim_id = dim["id"]
        w = dim["weight"]
        if dim_id in scores:
            total += scores[dim_id] * w
            total_w += w
    return round(total / total_w if total_w else 0.0, 3)


def score_scenario(scenario: dict, observation: dict | None, rubric: dict) -> dict:
    obs = observation or scenario.get("baseline_observation", {})
    raw_scores = obs.get("scores", {})
    normalized = {k: normalize_score(v) for k, v in raw_scores.items()}
    aggregate = weighted_aggregate(normalized, rubric)

    blocked = obs.get("result") == "blocked"
    thresholds = rubric.get("thresholds", {})
    status = "pass" if aggregate * 10 >= thresholds.get("auto_pass", 8.0) else (
        "review" if aggregate * 10 >= thresholds.get("human_review", 6.0) else "blocked"
    )
    if blocked and status == "pass":
        status = "review"

    return {
        "scenario_id": scenario["id"],
        "title": scenario.get("title", ""),
        "priority": scenario.get("priority", "P2"),
        "linked_opts": scenario.get("linked_opts", []),
        "observation_date": obs.get("date", ""),
        "result": obs.get("result", "unknown"),
        "blocked_step": obs.get("blocked_step"),
        "notes": obs.get("notes", ""),
        "scores_raw": raw_scores,
        "scores_normalized": normalized,
        "aggregate": aggregate,
        "aggregate_display": round(aggregate * 10, 1),
        "status": status,
    }


def filter_by_opt(scenarios: list[dict], opt_id: str, registry: dict) -> list[dict]:
    opt = registry.get("items", {}).get(opt_id, {})
    target = opt.get("scenario")
    if not target:
        return []
    return [s for s in scenarios if s["id"] == target]


def build_report(run_id: str, results: list[dict], rubric: dict) -> str:
    all_agg = [r["aggregate"] for r in results]
    overall = round(sum(all_agg) / len(all_agg), 3) if all_agg else 0.0
    p0 = [r for r in results if r.get("priority") == "P0"]
    p0_pass = sum(1 for r in p0 if r["status"] == "pass")
    blocked = [r for r in results if r["status"] == "blocked"]

    lines = [
        f"# 主链路 E2E 评测报告",
        "",
        f"| 项目 | 值 |",
        f"|------|-----|",
        f"| 运行 ID | `{run_id}` |",
        f"| 时间 | {datetime.now().strftime('%Y-%m-%d %H:%M')} |",
        f"| 场景数 | {len(results)} |",
        f"| 综合评分 | **{overall * 10:.1f}** / 10 |",
        f"| P0 通过率 | {p0_pass}/{len(p0)} |",
        f"| 阻断场景 | {len(blocked)} |",
        "",
        "## 场景明细",
        "",
        "| 场景 | 优先级 | 评分 | 状态 | 阻断步骤 | 关联 OPT |",
        "|------|--------|------|------|----------|----------|",
    ]
    for r in results:
        opts = ", ".join(r.get("linked_opts", []))
        lines.append(
            f"| {r['scenario_id']} | {r['priority']} | {r['aggregate_display']} | "
            f"{r['status']} | {r.get('blocked_step') or '-'} | {opts} |"
        )

    if blocked:
        lines += ["", "## 阻断项", ""]
        for r in blocked:
            lines.append(f"- **{r['scenario_id']}** ({r['title']}): {r.get('notes', '')}")

    lines += ["", "## 维度均分", ""]
    dim_sums: dict[str, list[float]] = {}
    for r in results:
        for dim, val in r.get("scores_normalized", {}).items():
            dim_sums.setdefault(dim, []).append(val)
    for dim in rubric["dimensions"]:
        dim_id = dim["id"]
        vals = dim_sums.get(dim_id, [])
        avg = round(sum(vals) / len(vals) * 10, 1) if vals else 0.0
        lines.append(f"- **{dim['name']}** ({dim_id}): {avg}/10")

    lines += [
        "",
        "## 下一步",
        "",
        "1. PM 在平台复测各场景，将观测写入 `inputs/feedback/observations/{run_id}.yaml`",
        "2. 修复 P0 关联 OPT，状态改为 `ready_for_regression`",
        "3. 触发 `loops/OPT回归循环.yaml`",
        "",
        f"产品核心锚点: `artifacts/产品定义/产品核心定义.md`",
    ]
    return "\n".join(lines)


def write_run_lock(run_id: str, results: list[dict], overall: float) -> None:
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    lock = {
        "run_id": run_id,
        "loop": "主链路E2E评测循环",
        "timestamp": datetime.now().isoformat(),
        "core_version": (ROOT / ".core-version").read_text(encoding="utf-8").strip(),
        "product_core": "artifacts/产品定义/产品核心定义.md",
        "rubric": "eval-data/rubrics/主链路评测量规.yaml",
        "scenarios": [r["scenario_id"] for r in results],
        "aggregate_score": overall,
        "evidence": {
            "results": results,
        },
    }
    dump_yaml(lock, run_dir / "run-lock.yaml")
    dump_yaml(
        {"run_id": run_id, "aggregate": overall, "scenario_count": len(results)},
        MEMORY / f"{run_id}.yaml",
    )
    active = ROOT / "runs" / "active"
    active.mkdir(parents=True, exist_ok=True)
    dump_yaml(lock, active / "run-lock.yaml")


def main() -> None:
    parser = argparse.ArgumentParser(description="主链路 E2E 评测")
    parser.add_argument("--observation", type=Path, help="PM 观测 YAML（覆盖 baseline）")
    parser.add_argument("--list", action="store_true", help="列出 scenario")
    parser.add_argument("--opt", type=str, help="OPT 回归模式，如 OPT-003")
    args = parser.parse_args()

    if args.list:
        for p in list_scenarios():
            s = load_yaml(p)
            print(f"{s['id']}\t{s.get('title', '')}\t{s.get('priority', '')}")
        return

    rubric = load_rubric()
    registry = load_yaml(OPT_REGISTRY) if OPT_REGISTRY.exists() else {"items": {}}

    scenarios: list[dict] = []
    for p in list_scenarios():
        scenarios.append(load_yaml(p))

    obs_override: dict[str, dict] = {}
    if args.observation and args.observation.exists():
        obs_data = load_yaml(args.observation)
        for item in obs_data.get("observations", []):
            obs_override[item["scenario_id"]] = item

    if args.opt:
        scenarios = filter_by_opt(scenarios, args.opt, registry)
        if not scenarios:
            raise SystemExit(f"OPT {args.opt} 无关联 scenario")

    results = []
    for s in scenarios:
        obs = obs_override.get(s["id"])
        results.append(score_scenario(s, obs, rubric))

    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    overall = round(sum(r["aggregate"] for r in results) / len(results), 3) if results else 0.0

    report = build_report(run_id, results, rubric)
    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS / f"E2E评测报告_{run_id}.md"
    report_path.write_text(report, encoding="utf-8")

    write_run_lock(run_id, results, overall)

    print(f"运行 ID: {run_id}")
    print(f"综合评分: {overall * 10:.1f}/10")
    print(f"报告: {report_path.relative_to(ROOT)}")
    for r in results:
        print(f"  {r['scenario_id']}: {r['aggregate_display']} ({r['status']})")


if __name__ == "__main__":
    main()
