"""软件优化智能体实验脚手架（支持热点剖析、调用链上下文与有界多轮执行反馈）。

推荐对比实验命令：
1. 仅开启热点剖析（单轮）：
    python3 agent_lab/agent_starter.py --use-profiler --max-rounds 1 --output-dir workspace/prof_only

2. 开启热点剖析 + 上下游调用链视图（单轮）：
    python3 agent_lab/agent_starter.py --use-profiler --use-call-chain --max-rounds 1 --output-dir workspace/prof_chain

3. 完整轻量智能体（热点剖析 + 调用链视图 + 最多 3 轮执行反馈迭代）：
    python3 agent_lab/agent_starter.py --use-profiler --use-call-chain --max-rounds 3 --output-dir workspace/full_agent

注意信息隔离边界：
- 智能体只允许读取任务目录下的 target.py、test_target.py 与 workload.py 运行反馈，
  严禁读取 benchmark/reference_patches/ 下的参考补丁。
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import config  # type: ignore
except ImportError:
    import config_template as config  # type: ignore

from openai import OpenAI
from profiler_tools import extract_static_call_graph, format_diagnostic_report, profile_task_dir

BENCHMARK_DIR = ROOT_DIR / "benchmark"
TASKS_ROOT = BENCHMARK_DIR / "tasks"
FENCE = chr(96) * 3
CODE_BLOCK_RE = re.compile(FENCE + r"(?:python)?\s*\n(.*?)" + FENCE, re.DOTALL)

_SANDBOX_CHECK = """
import hashlib, json, time, sys
from pathlib import Path

work_dir = Path(sys.argv[1]).resolve()
repeats = int(sys.argv[2])
sys.path.insert(0, str(work_dir))

import workload
warm = workload.build_inputs()
out = workload.run_workload(warm)
digest = hashlib.sha256(repr(out).encode("utf-8")).hexdigest()

samples = []
for _ in range(repeats):
    inp = workload.build_inputs()
    t0 = time.perf_counter()
    workload.run_workload(inp)
    t1 = time.perf_counter()
    samples.append((t1 - t0) * 1000.0)

print(json.dumps({"digest": digest, "samples_ms": samples}))
"""


def extract_python_code(text: str) -> str:
    matches = CODE_BLOCK_RE.findall(text)
    if matches:
        return max(matches, key=len).strip() + "\n"
    return text.strip() + "\n"


def verify_candidate_in_sandbox(
    task_dir: Path,
    candidate_code: str | None,
    base_digest: str | None = None,
    repeats: int = 3,
) -> dict[str, Any]:
    """在临时目录运行单元测试、计算工作负载摘要与耗时，必要时返回最新剖析信息。"""
    with tempfile.TemporaryDirectory(prefix="pyopt_agent_") as tmp:
        tmp_path = Path(tmp)
        for item in task_dir.iterdir():
            if item.is_file() and item.suffix == ".py":
                shutil.copy2(item, tmp_path / item.name)
        if candidate_code is not None:
            (tmp_path / "target.py").write_text(candidate_code, encoding="utf-8")

        test_proc = subprocess.run(
            [sys.executable, "-m", "unittest", "test_target.py"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            timeout=25.0,
            check=False,
        )
        if test_proc.returncode != 0:
            return {
                "ok": False,
                "stage": "unit_test",
                "error": (test_proc.stderr or test_proc.stdout).strip()[-1200:],
            }

        bench_proc = subprocess.run(
            [sys.executable, "-c", _SANDBOX_CHECK, str(tmp_path), str(repeats)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            timeout=25.0,
            check=False,
        )
        if bench_proc.returncode != 0:
            return {
                "ok": False,
                "stage": "workload_runtime",
                "error": (bench_proc.stderr or bench_proc.stdout).strip()[-1200:],
            }

        data = json.loads(bench_proc.stdout)
        if base_digest is not None and data["digest"] != base_digest:
            return {
                "ok": False,
                "stage": "semantic_equivalence",
                "error": "单元测试通过，但在完整工作负载上的返回值与原版不一致，请检查边界逻辑或缓存失效条件。",
            }

        prof = profile_task_dir(tmp_path, top_k=5)
        return {
            "ok": True,
            "digest": data["digest"],
            "median_ms": statistics.median(data["samples_ms"]),
            "profile": prof,
        }


def build_initial_prompt(
    meta: dict[str, Any],
    source_code: str,
    diagnostic_text: str,
) -> str:
    parts = [
        "请你作为软件性能优化智能体，优化下方 Python 模块 target.py 的执行效率。",
        "",
        "【硬性约束】",
        "1. 必须保持所有公开类、方法与函数的名称、参数签名、返回值类型和异常语义不变；",
        "2. 注意检查可变状态更新（如增删边、覆盖配置、输入字典不可变性等）下的缓存一致性；",
        "3. 仅可使用 Python 标准库；",
        f"4. 先用简短几句话写出你的【瓶颈归因与修改计划】（指出真正造成重复开销的调用链位置），随后在单个 {FENCE}python ... {FENCE} 代码块中给出完整的 target.py 源码。",
        "",
        f"【任务信息】{meta['task_id']} - {meta['summary']}（入口：{meta['entry_function']}）",
    ]
    if diagnostic_text:
        parts.extend(["", diagnostic_text])
    parts.extend(["", "【原始 target.py 源码】", f"{FENCE}python\n{source_code}\n{FENCE}"])
    return "\n".join(parts)


def run_agent_on_task(
    client: OpenAI,
    meta: dict[str, Any],
    use_profiler: bool,
    use_call_chain: bool,
    max_rounds: int,
    target_speedup: float,
) -> tuple[str, dict[str, Any]]:
    tid = meta["task_id"]
    task_dir = TASKS_ROOT / tid
    orig_code = (task_dir / "target.py").read_text(encoding="utf-8")

    base_check = verify_candidate_in_sandbox(task_dir, candidate_code=None, repeats=3)
    if not base_check["ok"]:
        raise RuntimeError(f"基线任务自检失败 {tid}: {base_check}")
    base_ms = float(base_check["median_ms"])
    base_digest = str(base_check["digest"])

    prof_data = base_check["profile"] if use_profiler else None
    graph_data = extract_static_call_graph(orig_code) if use_call_chain else None
    diag_text = format_diagnostic_report(prof_data, graph_data)

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "你是一名擅长动态剖析与跨函数调用链分析的软件性能优化智能体。"
                "请优先消除外层循环中的重复解析、重复编译、冗余深拷贝、低效线性查找或重复子问题计算，"
                "并严格保证所有边界与状态变更语义等价。"
            ),
        },
        {
            "role": "user",
            "content": build_initial_prompt(meta, orig_code, diag_text),
        },
    ]

    # 可扩展位置（供同学们在第一周小练习或第六周拓展中改造）：
    # 1. 可在此处加入自定义优化模式检查清单（Strategy Checklist）或历史案例检索；
    # 2. 可增加工具调用让模型按需读取 test_target.py / workload.py 的公开接口契约；
    # 3. 可改进多候选采样、回退策略或反思提示词结构。

    best_code = orig_code
    best_speedup = 1.0
    rounds_log: list[dict[str, Any]] = []
    prompt_tokens = 0
    completion_tokens = 0

    for r_idx in range(1, max_rounds + 1):
        resp = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,  # type: ignore[arg-type]
            temperature=config.DEFAULT_TEMPERATURE,
            max_tokens=config.DEFAULT_MAX_TOKENS,
        )
        reply = resp.choices[0].message.content or ""
        if resp.usage:
            prompt_tokens += resp.usage.prompt_tokens
            completion_tokens += resp.usage.completion_tokens

        cand_code = extract_python_code(reply)
        check = verify_candidate_in_sandbox(task_dir, cand_code, base_digest=base_digest, repeats=3)
        messages.append({"role": "assistant", "content": reply})

        if not check["ok"]:
            rounds_log.append(
                {
                    "round": r_idx,
                    "passed": False,
                    "stage": check["stage"],
                    "error": check["error"],
                }
            )
            print(f"  [{tid}] 第 {r_idx} 轮未通过 ({check['stage']})，准备反馈修正...")
            if r_idx < max_rounds:
                feedback = (
                    f"你上一轮提交的 target.py 未通过验证（阶段：{check['stage']}）。\n"
                    f"错误信息如下：\n{FENCE}\n{check['error']}\n{FENCE}\n"
                    "请定位导致错误的原因，修复语义或边界问题，并重新输出完整的 target.py 代码块。"
                )
                messages.append({"role": "user", "content": feedback})
            continue

        cand_ms = float(check["median_ms"])
        speedup = base_ms / max(cand_ms, 1e-6)
        rounds_log.append(
            {
                "round": r_idx,
                "passed": True,
                "cand_ms": round(cand_ms, 2),
                "speedup": round(speedup, 2),
            }
        )
        print(f"  [{tid}] 第 {r_idx} 轮验证通过！沙盒加速比: {speedup:.2f}x ({base_ms:.1f}ms -> {cand_ms:.1f}ms)")

        if speedup > best_speedup:
            best_speedup = speedup
            best_code = cand_code

        if speedup >= target_speedup or r_idx >= max_rounds:
            break

        next_diag = format_diagnostic_report(check["profile"] if use_profiler else None, None)
        feedback = (
            f"当前版本已通过全部正确性验证，实测加速比为 {speedup:.2f}x，尚未达到目标加速阈值 {target_speedup:.2f}x。\n"
            f"{next_diag}\n\n"
            "请结合上述最新剖析信息，检查是否仍有残余的跨函数重复计算或低效数据结构，输出进一步优化后的完整 target.py。"
        )
        messages.append({"role": "user", "content": feedback})

    trace = {
        "task_id": tid,
        "base_ms": round(base_ms, 2),
        "best_sandbox_speedup": round(best_speedup, 2),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "rounds": rounds_log,
    }
    return best_code, trace


def main() -> None:
    parser = argparse.ArgumentParser(description="运行可配置的软件性能优化智能体。")
    parser.add_argument("--task", type=str, default=None, help="仅运行单个 task_id")
    parser.add_argument("--use-profiler", action="store_true", help="接入 cProfile 动态热点剖析")
    parser.add_argument("--use-call-chain", action="store_true", help="接入 AST 静态上下游调用链拓扑")
    parser.add_argument("--max-rounds", type=int, default=3, help="最大生成与验证迭代轮数（默认 3）")
    parser.add_argument("--target-speedup", type=float, default=2.0, help="沙盒加速比达到该值后提前结束当前任务迭代")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT_DIR / "workspace" / "full_agent",
        help="最优候选代码保存目录",
    )
    args = parser.parse_args()

    if not config.API_KEY:
        raise SystemExit(
            "未检测到 API_KEY。请先复制 config_template.py 为 config.py 并填入密钥，"
            "或设置环境变量 ROTATION_API_KEY。"
        )

    tasks_meta = json.loads((BENCHMARK_DIR / "tasks.json").read_text(encoding="utf-8"))
    selected = [t for t in tasks_meta if args.task is None or t["task_id"] == args.task]
    if not selected:
        raise SystemExit(f"未匹配到任务: {args.task}")

    client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)
    traces: list[dict[str, Any]] = []

    for meta in selected:
        tid = meta["task_id"]
        print(
            f"[Agent] 开始优化 {tid} "
            f"(profiler={args.use_profiler}, call_chain={args.use_call_chain}, max_rounds={args.max_rounds})"
        )
        best_code, trace = run_agent_on_task(
            client=client,
            meta=meta,
            use_profiler=args.use_profiler,
            use_call_chain=args.use_call_chain,
            max_rounds=max(1, args.max_rounds),
            target_speedup=args.target_speedup,
        )
        out_file = args.output_dir / tid / "target.py"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(best_code, encoding="utf-8")
        traces.append(trace)

    trace_path = ROOT_DIR / "outputs" / f"{args.output_dir.name}_trace.json"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(json.dumps(traces, ensure_ascii=False, indent=2), encoding="utf-8")

    tot_in = sum(t["prompt_tokens"] for t in traces)
    tot_out = sum(t["completion_tokens"] for t in traces)
    print("\n=== 智能体运行结束 ===")
    print(f"候选目录: {args.output_dir}")
    print(f"轨迹日志: {trace_path}")
    print(f"累计输入 Token: {tot_in}, 累计输出 Token: {tot_out}")
    print(f"下一步请运行独立评测:\n  python3 agent_lab/evaluate.py --candidate-dir {args.output_dir}")


if __name__ == "__main__":
    main()
