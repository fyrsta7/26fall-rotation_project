"""使用开源 Codex CLI 外壳（底层可挂载 DeepSeek API 或课题组门户）批量运行优化任务。

工作原理：
1. 为每道基准题目在 workspace/<实验名>/<task_id>/ 下创建独立工作副本（仅复制 target.py、workload.py、test_target.py，严格隔离 reference_patches/）；
2. 调用 `codex exec` 非交互模式在独立目录中自动执行提示词（模型可自主读写文件、运行剖析与单元测试）；
3. 全部任务运行完毕后，可直接通过 `agent_lab/evaluate.py` 统一汇总评测指标。

示例命令：
    # 运行朴素提示词对照
    python3 agent_lab/run_codex_batch.py \
      --prompt-file agent_lab/prompts/naive_prompt.txt \
      --output-dir workspace/codex_naive

    # 运行你在手动交互中打磨好的引导式提示词
    python3 agent_lab/run_codex_batch.py \
      --prompt-file agent_lab/prompts/guided_agent_prompt.txt \
      --output-dir workspace/codex_guided

    # 统一评测对比
    python3 agent_lab/evaluate.py --candidate-dir workspace/codex_naive
    python3 agent_lab/evaluate.py --candidate-dir workspace/codex_guided
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = ROOT_DIR / "benchmark"
TASKS_ROOT = BENCHMARK_DIR / "tasks"


def prepare_isolated_workspace(task_id: str, dst_dir: Path) -> None:
    """将单个任务的待优化文件复制到隔离目录，不暴露参考答案。"""
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    src_dir = TASKS_ROOT / task_id
    for name in ("target.py", "workload.py", "test_target.py"):
        shutil.copy2(src_dir / name, dst_dir / name)


def main() -> None:
    parser = argparse.ArgumentParser(description="使用 Codex CLI 外壳批量运行 PyOpt-Lite 代码优化任务。")
    parser.add_argument(
        "--prompt-file",
        type=Path,
        default=ROOT_DIR / "agent_lab" / "prompts" / "guided_agent_prompt.txt",
        help="提示词模板文件路径",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT_DIR / "workspace" / "codex_guided",
        help="隔离工作区与优化后代码输出目录",
    )
    parser.add_argument("--task", type=str, default=None, help="仅运行指定 task_id（调试单题时使用）")
    parser.add_argument("--model", type=str, default=None, help="可选覆盖 Codex 使用的模型名，如 deepseek-flash")
    parser.add_argument("--codex-bin", type=str, default="codex", help="codex 可执行文件名称或路径")
    parser.add_argument("--timeout", type=int, default=300, help="单道任务超时秒数（默认 300 秒）")
    parser.add_argument("--prepare-only", action="store_true", help="仅初始化隔离工作副本（供 Qoder 等图形客户端手动对话修改），不自动调用 CLI")
    parser.add_argument("--dry-run", action="store_true", help="仅创建隔离目录并打印将执行的命令，不实际发起调用")
    args = parser.parse_args()

    if not args.prompt_file.exists():
        raise SystemExit(f"未找到提示词文件: {args.prompt_file}")
    base_prompt = args.prompt_file.read_text(encoding="utf-8").strip()

    if not args.dry_run and not args.prepare_only and shutil.which(args.codex_bin) is None:
        raise SystemExit(
            f"未在 PATH 中找到 `{args.codex_bin}`。请先参考 docs/01_api_and_agent_guide.md 安装 `@openai/codex` "
            "并配置好 DeepSeek 或课题组门户 API。"
        )

    tasks_meta = json.loads((BENCHMARK_DIR / "tasks.json").read_text(encoding="utf-8"))
    selected = [t for t in tasks_meta if args.task is None or t["task_id"] == args.task]
    if not selected:
        raise SystemExit(f"未匹配到任务: {args.task}")

    records = []
    for meta in selected:
        tid = meta["task_id"]
        work_dir = args.output_dir.resolve() / tid
        prepare_isolated_workspace(tid, work_dir)
        if args.prepare_only:
            print(f"[Prepare] 已创建手动实验目录: {work_dir}")
            continue

        full_prompt = (
            f"任务编号：{tid}\n"
            f"任务说明：{meta['summary']}（核心入口：{meta['entry_function']}）\n\n"
            f"{base_prompt}\n"
        )
        log_file = work_dir / "codex_last_message.txt"
        cmd = [
            args.codex_bin,
            "exec",
            "--skip-git-repo-check",
            "--cd",
            str(work_dir),
            "-c",
            'sandbox_mode="workspace-write"',
            "-o",
            str(log_file),
        ]
        if args.model:
            cmd.extend(["-m", args.model])
        cmd.append(full_prompt)

        if args.dry_run:
            print(f"[Dry-Run] 已准备隔离目录 {work_dir}")
            print("  命令预览:", " ".join(cmd[:-1]), "<PROMPT>")
            continue

        print(f"[Codex Batch] 正在执行 {tid} ...")
        t0 = time.perf_counter()
        proc = subprocess.run(
            cmd,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=args.timeout,
            check=False,
        )
        elapsed = round(time.perf_counter() - t0, 2)
        (work_dir / "codex_stdout.log").write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")
        status = "ok" if proc.returncode == 0 else f"exit_{proc.returncode}"
        print(f"  [{tid}] 完成，状态={status}，耗时={elapsed}s")
        records.append({"task_id": tid, "status": status, "elapsed_sec": elapsed})

    if args.prepare_only:
        print(f"\n已准备手动交互工作区: {args.output_dir}")
        print(f"你可以在 Qoder 中打开对应子目录修改 target.py，随后运行评测:\n  python3 agent_lab/evaluate.py --candidate-dir {args.output_dir}")
    elif not args.dry_run:
        summary_path = ROOT_DIR / "outputs" / f"{args.output_dir.name}_batch_run.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\n=== 批量执行完成 ===")
        print(f"结果目录: {args.output_dir}")
        print(f"请运行统一评测查看得分:\n  python3 agent_lab/evaluate.py --candidate-dir {args.output_dir}")


if __name__ == "__main__":
    main()
