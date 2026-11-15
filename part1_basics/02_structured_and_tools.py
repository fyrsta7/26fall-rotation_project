"""示例 02：最小工具调用循环（理解编程智能体的核心运行机制）。

本脚本用不到 100 行代码展示现代编程智能体（Agent）的最小工作循环：
    给定目标 -> 模型决定调用哪个工具 -> 本地执行工具并返回观测结果 -> 模型继续推理直至给出结论。

运行方式：
    python3 part1_basics/02_structured_and_tools.py
"""

import json
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    import config  # type: ignore
except ImportError:
    import config_template as config  # type: ignore

from openai import OpenAI

# 模拟一个待诊断的小型代码仓库文件表
DEMO_FILES: dict[str, str] = {
    "router.py": (
        "import re\n"
        "from matcher import check_pattern\n\n"
        "def route_all(lines, rules):\n"
        "    matched = []\n"
        "    for line in lines:\n"
        "        for name, expr in rules:\n"
        "            if check_pattern(expr, line):\n"
        "                matched.append((name, line))\n"
        "                break\n"
        "    return matched\n"
    ),
    "matcher.py": (
        "import re\n\n"
        "def check_pattern(expr, text):\n"
        "    # 注意：每次调用都会重新解析正则语法树（当超过内部小缓存容量时尤为明显）\n"
        "    regex = re.compile(expr, re.IGNORECASE)\n"
        "    return regex.search(text) is not None\n"
    ),
}

DEMO_PROFILE = [
    {"function": "matcher.py:check_pattern", "calls": 200000, "self_ms": 410.2, "cum_ms": 980.5},
    {"function": "re.compile", "calls": 200000, "self_ms": 570.3, "cum_ms": 570.3},
    {"function": "router.py:route_all", "calls": 1, "self_ms": 45.1, "cum_ms": 1025.6},
]

TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_hotspot_profile",
            "description": "获取当前工作负载下的性能剖析热点函数列表。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_source_file",
            "description": "按文件名读取源码内容，可选 router.py 或 matcher.py。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "源码文件名"}
                },
                "required": ["filename"],
            },
        },
    },
]


def execute_local_tool(name: str, arguments: dict[str, Any]) -> str:
    if name == "get_hotspot_profile":
        return json.dumps(DEMO_PROFILE, ensure_ascii=False, indent=2)
    if name == "read_source_file":
        fn = arguments.get("filename", "")
        return DEMO_FILES.get(fn, f"未找到文件: {fn}，可选文件: {list(DEMO_FILES)}")
    return f"未知工具: {name}"


def main() -> None:
    if not config.API_KEY:
        raise SystemExit(
            "未检测到 API_KEY。请先将 config_template.py 复制为 config.py 并填入密钥，"
            "或设置环境变量 ROTATION_API_KEY。"
        )

    client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "你是一名性能优化诊断智能体。请先查看性能剖析热点，再按需读取上下游源码，"
                "找出真正的性能瓶颈位置并说明应该联合修改哪几个函数。"
            ),
        },
        {
            "role": "user",
            "content": "请诊断当前项目的性能瓶颈，并给出跨函数修改建议（包含 router.py 与 matcher.py）。",
        },
    ]

    for step in range(1, 7):
        resp = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            temperature=0.1,
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            print(f"\n[第 {step} 步] 智能体完成诊断，输出最终结论：\n")
            print(msg.content)
            return

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            print(f"[第 {step} 步] 智能体调用工具: {call.function.name}({args})")
            observation = execute_local_tool(call.function.name, args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": observation,
                }
            )

    print("达到步数上限，循环结束。")


if __name__ == "__main__":
    main()
