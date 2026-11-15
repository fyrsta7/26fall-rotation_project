"""PyOpt-Lite 统一评测脚本（正确性单元测试 + 工作负载等价校验 + 多轮中位加速比统计）。

常用命令：
1. 查看基准原始耗时与参考优化补丁表现（自检）：
    python3 agent_lab/evaluate.py --use-reference

2. 评测某个实验目录生成的候选代码（目录结构支持 <dir>/<task_id>/target.py 或 <dir>/<task_id>.py）：
    python3 agent_lab/evaluate.py --candidate-dir workspace/direct
    python3 agent_lab/evaluate.py --candidate-dir workspace/agent --output outputs/agent_eval.json
"""

from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = ROOT_DIR / "benchmark"
TASKS_ROOT = BENCHMARK_DIR / "tasks"
REF_PATCHES_ROOT = BENCHMARK_DIR / "reference_patches"

_TIMING_DRIVER = """
import json, hashlib, time, sys
from pathlib import Path

work_dir = Path(sys.argv[1]).resolve()
repeats = int(sys.argv[2])
sys.path.insert(0, str(work_dir))

import workload

# 预热 1 次并计算确定性输出摘要
warm_inputs = workload.build_inputs()
out = workload.run_workload(warm_inputs)
digest = hashlib.sha256(repr(out).encode("utf-8")).hexdigest()

samples_ms = []
for _ in range(repeats):
    inp = workload.build_inputs()
    t0 = time.perf_counter()
    workload.run_workload(inp)
    t1 = time.perf_counter()
    samples_ms.append((t1 - t0) * 1000.0)

print(json.dumps({"digest": digest, "samples_ms": samples_ms}))
"""


def _run_in_temp_copy(
    base_task_dir: Path,
    override_target_code: str | None,
    repeats: int,
    timeout_sec: float = 30.0,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pyopt_eval_") as tmp:
        tmp_path = Path(tmp)
        for item in base_task_dir.iterdir():
            if item.is_file() and item.suffix == ".py":
                shutil.copy2(item, tmp_path / item.name)
        if override_target_code is not None:
            (tmp_path / "target.py").write_text(override_target_code, encoding="utf-8")

        test_proc = subprocess.run(
            [sys.executable, "-m", "unittest", "test_target.py"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        if test_proc.returncode != 0:
            return {
                "unit_test_passed": False,
                "error": (test_proc.stderr or test_proc.stdout).strip()[-1500:],
            }

        bench_proc = subprocess.run(
            [sys.executable, "-c", _TIMING_DRIVER, str(tmp_path), str(repeats)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        if bench_proc.returncode != 0:
            return {
                "unit_test_passed": False,
                "error": (bench_proc.stderr or bench_proc.stdout).strip()[-1500:],
            }

        payload = json.loads(bench_proc.stdout)
        samples = payload["samples_ms"]
        return {
            "unit_test_passed": True,
            "digest": payload["digest"],
            "median_ms": statistics.median(samples),
            "samples_ms": [round(x, 2) for x in samples],
        }


def resolve_candidate_code(candidate_dir: Path, task_id: str) -> str | None:
    nested = candidate_dir / task_id / "target.py"
    flat = candidate_dir / f"{task_id}.py"
    if nested.exists():
        return nested.read_text(encoding="utf-8")
    if flat.exists():
        return flat.read_text(encoding="utf-8")
    return None


def evaluate_single_task(
    task_id: str,
    candidate_code: str | None,
    repeats: int = 5,
    include_reference: bool = True,
) -> dict[str, Any]:
    task_dir = TASKS_ROOT / task_id
    base_res = _run_in_temp_copy(task_dir, override_target_code=None, repeats=repeats)
    if not base_res.get("unit_test_passed"):
        raise RuntimeError(f"基准任务 {task_id} 自身运行异常: {base_res.get('error')}")

    base_ms = float(base_res["median_ms"])
    base_digest = str(base_res["digest"])

    ref_speedup = None
    ref_file = REF_PATCHES_ROOT / f"{task_id}.py"
    if include_reference and ref_file.exists():
        ref_res = _run_in_temp_copy(
            task_dir,
            override_target_code=ref_file.read_text(encoding="utf-8"),
            repeats=repeats,
        )
        if ref_res.get("unit_test_passed") and ref_res.get("digest") == base_digest:
            ref_speedup = base_ms / max(float(ref_res["median_ms"]), 1e-6)

    if candidate_code is None:
        return {
            "task_id": task_id,
            "passed": False,
            "base_ms": round(base_ms, 2),
            "cand_ms": None,
            "speedup": 1.0,
            "ref_speedup": round(ref_speedup, 2) if ref_speedup else None,
            "opt_1_2x": False,
            "opt_ref": False,
            "error": "未找到候选 target.py",
        }

    cand_res = _run_in_temp_copy(task_dir, override_target_code=candidate_code, repeats=repeats)
    if not cand_res.get("unit_test_passed"):
        return {
            "task_id": task_id,
            "passed": False,
            "base_ms": round(base_ms, 2),
            "cand_ms": None,
            "speedup": 1.0,
            "ref_speedup": round(ref_speedup, 2) if ref_speedup else None,
            "opt_1_2x": False,
            "opt_ref": False,
            "error": cand_res.get("error", "测试未通过"),
        }

    if cand_res.get("digest") != base_digest:
        return {
            "task_id": task_id,
            "passed": False,
            "base_ms": round(base_ms, 2),
            "cand_ms": round(float(cand_res["median_ms"]), 2),
            "speedup": 1.0,
            "ref_speedup": round(ref_speedup, 2) if ref_speedup else None,
            "opt_1_2x": False,
            "opt_ref": False,
            "error": "工作负载返回值与原实现不一致（语义不等价）",
        }

    cand_ms = float(cand_res["median_ms"])
    raw_speedup = base_ms / max(cand_ms, 1e-6)
    opt_ref = bool(ref_speedup is not None and raw_speedup >= 0.85 * ref_speedup)
    return {
        "task_id": task_id,
        "passed": True,
        "base_ms": round(base_ms, 2),
        "cand_ms": round(cand_ms, 2),
        "speedup": round(raw_speedup, 2),
        "ref_speedup": round(ref_speedup, 2) if ref_speedup else None,
        "opt_1_2x": raw_speedup >= 1.20,
        "opt_ref": opt_ref,
        "error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="评测 PyOpt-Lite 候选优化结果。")
    parser.add_argument("--candidate-dir", type=Path, help="候选优化结果所在目录")
    parser.add_argument("--use-reference", action="store_true", help="使用 benchmark/reference_patches 作为候选进行基准校验")
    parser.add_argument("--task", type=str, default=None, help="仅评测单个 task_id")
    parser.add_argument("--repeats", type=int, default=5, help="每个版本重复计时次数（取中位数）")
    parser.add_argument("--output", type=Path, default=None, help="将详细评测结果保存为 JSON 文件")
    args = parser.parse_args()

    if not args.use_reference and args.candidate_dir is None:
        raise SystemExit("请指定 --candidate-dir <目录> 或使用 --use-reference 运行基准自检。")

    tasks_meta = json.loads((BENCHMARK_DIR / "tasks.json").read_text(encoding="utf-8"))
    selected = [t for t in tasks_meta if args.task is None or t["task_id"] == args.task]
    if not selected:
        raise SystemExit(f"未匹配到任务: {args.task}")

    source_dir = REF_PATCHES_ROOT if args.use_reference else args.candidate_dir
    assert source_dir is not None

    results: list[dict[str, Any]] = []
    bt = chr(96)
    print("| 任务 ID | 正确性 | 原始中位耗时 (ms) | 优化后耗时 (ms) | 有效加速比 | 参考补丁加速比 | Opt@1.2x | Opt_Ref |")
    print("| --- | :---: | ---: | ---: | ---: | ---: | :---: | :---: |")
    for meta in selected:
        tid = meta["task_id"]
        code = resolve_candidate_code(source_dir, tid)
        row = evaluate_single_task(tid, code, repeats=args.repeats, include_reference=True)
        results.append(row)
        status = "PASS" if row["passed"] else "FAIL"
        cand_str = f"{row['cand_ms']:.2f}" if row["cand_ms"] is not None else "-"
        ref_str = f"{row['ref_speedup']:.2f}x" if row["ref_speedup"] is not None else "-"
        print(
            f"| {bt}{tid}{bt} | {status} | {row['base_ms']:.2f} | {cand_str} | "
            f"{row['speedup']:.2f}x | {ref_str} | "
            f"{'是' if row['opt_1_2x'] else '否'} | {'是' if row['opt_ref'] else '否'} |"
        )

    n = len(results)
    pass_rate = sum(1 for r in results if r["passed"]) / n
    effective_speedups = [float(r["speedup"]) if r["passed"] else 1.0 for r in results]
    geomean_speedup = math.exp(sum(math.log(max(s, 1e-6)) for s in effective_speedups) / n)
    opt_1_2_rate = sum(1 for r in results if r["opt_1_2x"]) / n
    opt_ref_rate = sum(1 for r in results if r["opt_ref"]) / n

    summary = {
        "num_tasks": n,
        "pass_at_1": round(pass_rate, 4),
        "geomean_speedup": round(geomean_speedup, 3),
        "opt_at_1_2x": round(opt_1_2_rate, 4),
        "opt_ref": round(opt_ref_rate, 4),
        "tasks": results,
    }

    print("\n=== 汇总指标 ===")
    print(f"- 正确率 (Pass@1):            {pass_rate * 100:.1f}% ({sum(1 for r in results if r['passed'])}/{n})")
    print(f"- 几何平均有效加速比 (GeoMean): {geomean_speedup:.2f}x")
    print(f"- 有效优化率 (Opt@1.2x):      {opt_1_2_rate * 100:.1f}%")
    print(f"- 参考水平达成率 (Opt_Ref):    {opt_ref_rate * 100:.1f}%")

    failed = [r for r in results if not r["passed"]]
    if failed:
        print("\n=== 未通过任务摘要 ===")
        for r in failed:
            first_line = (r["error"] or "").splitlines()[-1] if r["error"] else "未知原因"
            print(f"- {r['task_id']}: {first_line}")

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n详细 JSON 评测结果已保存至: {args.output}")


if __name__ == "__main__":
    main()
