"""示例 01：最小大模型 API 调用与用量统计。

运行方式：
    python3 part1_basics/01_hello_api.py
"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    import config  # type: ignore
except ImportError:
    import config_template as config  # type: ignore

from openai import OpenAI


def main() -> None:
    if not config.API_KEY:
        raise SystemExit(
            "未检测到 API_KEY。请先将 config_template.py 复制为 config.py 并填入密钥，"
            "或设置环境变量 ROTATION_API_KEY。"
        )

    client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)
    response = client.chat.completions.create(
        model=config.MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是一名软件性能优化助手，回答简洁准确。",
            },
            {
                "role": "user",
                "content": "请用三句话解释为什么在高频循环内部重复编译正则表达式会拖慢 Python 程序。",
            },
        ],
        temperature=config.DEFAULT_TEMPERATURE,
        max_tokens=512,
    )

    print("=== 模型回复 ===")
    print(response.choices[0].message.content)

    if response.usage:
        print("\n=== Token 用量统计 ===")
        print(f"输入 Token 数 (prompt_tokens):     {response.usage.prompt_tokens}")
        print(f"输出 Token 数 (completion_tokens): {response.usage.completion_tokens}")
        print(f"总计 Token 数 (total_tokens):      {response.usage.total_tokens}")
        cache_hit = getattr(response.usage, "prompt_cache_hit_tokens", None)
        if cache_hit is not None:
            print(f"前缀缓存命中 (cache_hit_tokens):   {cache_hit}")


if __name__ == "__main__":
    main()
