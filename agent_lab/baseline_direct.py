"""基线方法：单轮 Direct Prompt 代码性能优化。

不提供动态性能剖析数据，不提供调用链拓扑，也不执行多轮测试反馈，
仅将待优化模块的源码直接交给大模型进行单次重写。

运行方式：
    python3 agent_lab/baseline_direct.py
    python3 agent_lab/evaluate.py --candidate-dir workspace/direct
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    import config  # type: ignore
except ImportError:
    import config_template as config  # type: ignore

from openai import OpenAI

BENCHMARK_DIR = ROOT_DIR / "benchmark"
TASKS_ROOT = BENCHMARK_DIR / "tasks"

FENCE = chr(96) * 3
CODE_BLOCK_RE = re.compile(FENCE + r"(?:python)?\s*\n(.*?)" + FENCE, re.DOTALL)


def extract_python_code(response_text: str) -> str:
    matches = CODE_BLOCK_RE.findall(response_text)
    if matches:
        return max(matches, key=len).strip() + "\n"
    return response_text.strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="运行单轮 Direct Prompt 优化基线。")
    parser.add_argument("--task", type=str, default=None, help="仅运行指定 task_id")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT_DIR / "workspace" / "direct",
        help="优化后候选代码输出目录",
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
    total_prompt_tokens = 0
    total_completion_tokens = 0

    for meta in selected:
        tid = meta["task_id"]
        source_code = (TASKS_ROOT / tid / "target.py").read_text(encoding="utf-8")
        prompt = (
            "请优化下面这个 Python 模块（target.py）的运行性能。\n"
            "严格要求：\n"
            "1. 保持所有公开类、函数签名、返回值结构、异常类型及边界行为完全不变；\n"
            "2. 仅允许使用 Python 标准库；\n"
            f"3. 请在单个 {FENCE}python ... {FENCE} 代码块中输出完整的优化后 target.py 源码。\n\n"
            f"任务简介：{meta['summary']}\n"
            f"入口函数：{meta['entry_function']}\n\n"
            "原始 target.py 源码：\n"
            f"{FENCE}python\n{source_code}\n{FENCE}"
        )

        print(f"[Direct] 正在生成 {tid} ...")
        resp = client.chat.completions.create(
            model=config.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是一名严谨的软件性能优化专家，只输出语义等价且更高效的完整 Python 模块代码。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=config.DEFAULT_TEMPERATURE,
            max_tokens=config.DEFAULT_MAX_TOKENS,
        )
        content = resp.choices[0].message.content or ""
        candidate_code = extract_python_code(content)

        out_file = args.output_dir / tid / "target.py"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(candidate_code, encoding="utf-8")

        if resp.usage:
            total_prompt_tokens += resp.usage.prompt_tokens
            total_completion_tokens += resp.usage.completion_tokens

    print("\n=== Direct 基线生成完成 ===")
    print(f"候选目录: {args.output_dir}")
    print(f"累计输入 Token: {total_prompt_tokens}, 累计输出 Token: {total_completion_tokens}")
    print(f"下一步请运行评测:\n  python3 agent_lab/evaluate.py --candidate-dir {args.output_dir}")


if __name__ == "__main__":
    main()
