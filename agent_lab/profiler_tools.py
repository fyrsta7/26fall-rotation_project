"""性能剖析与调用链上下文提取工具库。

既可在命令行单独运行以观察某个任务的瓶颈：
    python3 agent_lab/profiler_tools.py --task task_01_log_router
也可在自定义优化智能体中直接 import 调用。
"""

from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
TASKS_ROOT = ROOT_DIR / "benchmark" / "tasks"

_PROFILE_SNIPPET = """
import cProfile, json, pstats, sys
from pathlib import Path

task_dir = Path(sys.argv[1]).resolve()
top_k = int(sys.argv[2])
sys.path.insert(0, str(task_dir))

import workload
inputs = workload.build_inputs()
prof = cProfile.Profile()
prof.enable()
workload.run_workload(inputs)
prof.disable()

stats = pstats.Stats(prof)
entries = []
for func, (cc, nc, tt, ct, callers) in stats.stats.items():
    filename, lineno, func_name = func
    caller_list = []
    for c_func, c_val in callers.items():
        c_file, c_line, c_name = c_func
        c_ncalls = c_val[0] if isinstance(c_val, tuple) else int(c_val)
        caller_list.append({
            "caller": c_name,
            "file": Path(c_file).name if not c_file.startswith("<") else c_file,
            "line": c_line,
            "calls": c_ncalls,
        })
    caller_list.sort(key=lambda x: x["calls"], reverse=True)
    entries.append({
        "function": func_name,
        "file": Path(filename).name if not filename.startswith("<") else filename,
        "is_target_module": Path(filename).name == "target.py",
        "line": lineno,
        "primitive_calls": cc,
        "total_calls": nc,
        "self_ms": round(tt * 1000.0, 3),
        "cum_ms": round(ct * 1000.0, 3),
        "top_callers": caller_list[:4],
    })

entries.sort(key=lambda x: (x["cum_ms"], x["self_ms"]), reverse=True)
target_entries = [e for e in entries if e["is_target_module"]]
builtin_entries = [e for e in entries if not e["is_target_module"] and e["self_ms"] >= 1.0]
print(json.dumps({
    "target_hotspots": target_entries[:top_k],
    "external_or_builtin_hotspots": builtin_entries[:top_k],
}, ensure_ascii=False))
"""


def profile_task_dir(task_dir: Path, top_k: int = 8, timeout_sec: float = 30.0) -> dict[str, Any]:
    """在独立子进程中运行 workload 并采集 cProfile 热点与动态调用来源。"""
    proc = subprocess.run(
        [sys.executable, "-c", _PROFILE_SNIPPET, str(task_dir), str(top_k)],
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    if proc.returncode != 0:
        return {"error": proc.stderr.strip() or "cProfile 执行失败"}
    return json.loads(proc.stdout)


def extract_static_call_graph(source_code: str) -> dict[str, dict[str, Any]]:
    """解析 target.py 源码，提取每个函数/方法的行号范围、下游调用列表与上游调用方列表。"""
    tree = ast.parse(source_code)
    defs: dict[str, dict[str, Any]] = {}

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.class_stack: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            qname = f"{'.'.join(self.class_stack)}.{node.name}" if self.class_stack else node.name
            callees: list[str] = []
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    if isinstance(sub.func, ast.Name):
                        callees.append(sub.func.id)
                    elif isinstance(sub.func, ast.Attribute):
                        callees.append(sub.func.attr)
            defs[qname] = {
                "short_name": node.name,
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "raw_callees": sorted(set(callees)),
                "callees": [],
                "callers": [],
            }

    Visitor().visit(tree)
    short_to_qnames: dict[str, list[str]] = {}
    for qname, info in defs.items():
        short_to_qnames.setdefault(info["short_name"], []).append(qname)

    for qname, info in defs.items():
        resolved_callees: list[str] = []
        for raw in info["raw_callees"]:
            for target_qname in short_to_qnames.get(raw, ()):
                resolved_callees.append(target_qname)
                if qname not in defs[target_qname]["callers"]:
                    defs[target_qname]["callers"].append(qname)
        info["callees"] = sorted(set(resolved_callees))
        del info["raw_callees"]

    return defs


def format_diagnostic_report(
    profile_data: dict[str, Any] | None,
    call_graph: dict[str, dict[str, Any]] | None,
) -> str:
    """将热点剖析与调用链关系格式化为供智能体阅读的简洁诊断摘要。"""
    sections: list[str] = []
    if profile_data:
        if "error" in profile_data:
            sections.append(f"【动态性能剖析异常】\n{profile_data['error']}")
        else:
            lines = ["【动态性能剖析 (cProfile) - target.py 内部函数耗时排行】"]
            for item in profile_data.get("target_hotspots", []):
                caller_desc = ", ".join(
                    f"{c['file']}:{c['caller']}({c['calls']}次)" for c in item.get("top_callers", [])
                )
                lines.append(
                    f"- {item['function']} (行 {item['line']}): "
                    f"调用 {item['total_calls']} 次, 自身耗时 {item['self_ms']} ms, "
                    f"累计耗时 {item['cum_ms']} ms | 主要调用方: {caller_desc or '入口'}"
                )
            ext = profile_data.get("external_or_builtin_hotspots", [])
            if ext:
                lines.append("\n【动态性能剖析 - 高耗时标准库/内置调用】")
                for item in ext[:5]:
                    caller_desc = ", ".join(
                        f"{c['file']}:{c['caller']}({c['calls']}次)" for c in item.get("top_callers", [])
                    )
                    lines.append(
                        f"- {item['file']}:{item['function']}: "
                        f"调用 {item['total_calls']} 次, 自身耗时 {item['self_ms']} ms, "
                        f"累计耗时 {item['cum_ms']} ms | 触发位置: {caller_desc}"
                    )
            sections.append("\n".join(lines))

    if call_graph:
        lines = ["【静态调用链拓扑 (target.py 内部 Caller <-> Callee 关系)】"]
        for qname, info in call_graph.items():
            lines.append(
                f"- {qname} (行 {info['start_line']}-{info['end_line']}): "
                f"上游调用方={info['callers'] or ['外部入口']} -> 下游被调={info['callees'] or ['无内部被调']}"
            )
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(description="对指定基准任务运行热点剖析与调用链分析。")
    parser.add_argument("--task", required=True, help="任务 ID，例如 task_01_log_router")
    args = parser.parse_args()

    task_dir = TASKS_ROOT / args.task
    if not task_dir.exists():
        raise SystemExit(f"未找到任务目录: {task_dir}")

    prof = profile_task_dir(task_dir)
    graph = extract_static_call_graph((task_dir / "target.py").read_text(encoding="utf-8"))
    print(format_diagnostic_report(prof, graph))


if __name__ == "__main__":
    main()
