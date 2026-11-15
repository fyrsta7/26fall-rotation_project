"""大模型接口配置模板。

使用方法：
1. 将本文件复制为 config.py（config.py 已加入 .gitignore，不会被 Git 提交）；
2. 填入你选用的渠道配置，或直接通过环境变量 ROTATION_API_KEY / ROTATION_BASE_URL / ROTATION_MODEL 覆盖。
"""

import os

# ==================== 常用渠道参考 ====================
# 渠道 A：课题组大模型门户（联系负责人获取账号额度）
#   BASE_URL = "https://llm.xmcp.ltd"
#   MODEL    = "volc/deepseek-v3-250324"
#
# 渠道 B：DeepSeek 官方开放平台（推荐自备，充值 10 元即可完成全部基础实验）
#   BASE_URL = "https://api.deepseek.com"
#   MODEL    = "deepseek-chat"
#
# 渠道 C：阿里云百炼 / 千问 Token Plan（如 qwen4-max-preview，预览期折扣接近 DeepSeek）
#   常规兼容地址: "https://dashscope.aliyuncs.com/compatible-mode/v1"
#   Token Plan 专用地址: "https://token-plan.maas.qwencloudapi.com/v1"
# ======================================================

API_KEY = os.getenv("ROTATION_API_KEY", "")
BASE_URL = os.getenv("ROTATION_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("ROTATION_MODEL", "deepseek-chat")

# 单次请求默认生成上限与采样温度
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.2
