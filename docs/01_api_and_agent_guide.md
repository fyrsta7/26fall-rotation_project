# 从零认识大模型 API 与编程智能体（安装、配置与使用指南）

本文档面向第一周参加轮转的同学，默认大家此前没有接触过大模型接口或编程智能体。下文依次说明什么是 `API Key`、什么是 `Agent`（编程智能体）、各自如何免费或低成本获取，以及如何配置手动交互工具与自动化批量运行环境。

## 一、先分清两个基础概念：API Key 与 Agent

在日常科研与开发交流中，大家经常同时听到“调用大模型 API”和“使用编程 Agent”，两者处于不同层次：

| 概念 | 本质定义 | 具备的能力 | 自身局限 | 常见代表 |
| --- | --- | --- | --- | --- |
| 大模型 API（与 API Key） | 裸的大模型调用接口。程序通过网络发送一段文字，远端服务器上的模型返回一段生成的文字；`API Key`（接口密钥）则是调用该接口的身份与计费凭证。 | 基础的文本输入与文本输出能力（例如回答问题、根据你粘贴进去的代码片段返回一段修改后的代码）。 | 模型本身无法访问你电脑里的文件夹，不能自行打开源码文件，也不能在终端运行测试或测量程序耗时。 | 课题组大模型门户接口、DeepSeek 官方 API、阿里云百炼 API |
| 编程智能体（Agent） | 在裸 API 外层套上一层工程外壳。外壳程序为大模型配备了读写本地文件、检索代码库、执行终端命令等工具，并负责维护多步执行循环。 | 你只需输入任务目标，Agent 就能自行读取项目代码、运行性能剖析命令、修改源码文件，并根据测试报错自动返工修正。 | 底层依然需要消耗某个大模型的计算额度（由客户端内置赠送积分提供，或者填入你自己的 `API Key`）。 | 学校提供的 Qoder、免费积分客户端 WorkBuddy、付费订阅的 OpenAI Codex、以及挂载第三方 API 的开源 Codex CLI |

理解两者的分工之后，第一周实验中的工具组合就很清晰：

- 前期手动摸索阶段：打开自带图形界面与免费额度的 Agent 软件（如北大版 Qoder 或 WorkBuddy），针对单个优化任务开启对话，直接观察怎样的输入提示能够获得理想的加速补丁。
- 后期批量验证阶段：准备一个裸大模型 `API Key`（如充值 10 元 DeepSeek 或申请课题组门户），外层套上开源的 Codex CLI 命令行外壳（或运行 Python 驱动脚本），让脚本自动完成多道基准题目并汇总加速指标。

## 二、如何获取 API Key（裸模型接口渠道）

在编写自动化脚本或给开源命令行外壳配置底层模型时，任选以下一种途径获取 `API Key` 即可（请妥善保管个人密钥，切勿提交到公开 GitHub 仓库）：

1. 课题组大模型门户（组内统一额度）：通过微信或邮件联系第一周负责人（赵雨薇，`zhaoyuwei@stu.pku.edu.cn`）开通[课题组大模型门户](https://llm.xmcp.ltd/)账号，获取个人专属 `API_KEY` 与模型名称。课题组额度仅限本人科研轮转项目使用。
2. DeepSeek 官方开放平台（推荐自备，充值 10 元即可满足多轮实验）：前往 [DeepSeek 开放平台](https://platform.deepseek.com/) 注册账号并充值 10 元人民币即可创建密钥。运行完本仓库第一周全部 8 道基准题目的自动化对比实验，累计消耗通常只有 0.5 至 2 元人民币。
3. 其他可选模型 API 参考：
   - 国产高性价比进阶模型：腾讯云混元 `Hy4`（近期设有免费体验与 TokenHub 五折优惠）以及阿里云百炼 `qwen4-max-preview`（通过百炼 Token Plan 接入，折扣期折算单价与 DeepSeek 接近，夜间时段另有额外折扣）在复杂代码推理上的综合表现均优于基础版 DeepSeek。
   - 海外模型：Google 近期发布的 `Gemini 4` 系列（如 `Gemini 4 Argon`、`Gemini 3.8 Flash`）社区评价良好且官方接口定价相对实惠（参见 [Gemini API 定价说明](https://ai.google.dev/gemini-api/docs/pricing)）；OpenAI 近期部分模型在复杂代码细节保持上有所波动且调用单价偏贵；Anthropic 的 Claude 代码能力突出，但个人在国内网络环境下直接注册充值极易触发封号，确有对比需求时请统一通过课题组门户调用。

## 三、如何安装与配置编程智能体（Agent 外壳渠道）

根据使用场景（图形界面手动对话，或命令行脚本自动批处理），推荐以下三类 Agent 方案：

### 1. 学校免费提供：北大正版授权 Qoder（手动交互首选）

学校计算中心已与阿里云合作面向全校师生免费提供一年期正版 Qoder 编程智能体服务：

- 开通说明直达链接：[北京大学计算中心《关于提供Qoder编程智能体服务的通知》](https://cc.pku.edu.cn/notice/859.html)
- 客户端下载直达链接：[Qoder 国内版客户端下载页](https://qoder.cn/download)（支持 Windows、macOS 与 Linux）
- 额度说明：按通知指引完成校内身份与阿里云授权后，每个账号每月免费享有 3,000 Credits（额度用尽可申请增补；当月使用不足三分之一的闲置账号会被自动回收，重新申领即可恢复）。

### 2. 其他每日赠送积分的免费桌面 Agent

除学校提供的 Qoder 外，以下国产桌面 Agent 每日均赠送免费积分，日常手动开展实验同样充足：

- WorkBuddy / CodeBuddy（腾讯）：下载桌面客户端每日签到可领约 100 至 200 等值积分，且常设腾讯混元 `Hy4` 免费或优惠模型档位（注意优先选择 `Hy4` 或 `DeepSeek` 模型；若切换为 `Kimi` 等高倍率模型，赠送积分会迅速耗尽）。
- 千问办公（阿里）：访问 [千问办公官网](https://www.qwenwork.cn) 下载客户端，个人新用户注册赠送 2,000 积分，每日登录赠送 100 当日有效积分。
- 豆包工作（字节）：访问 [豆包工作页面](https://www.doubao.com/work/) 或在豆包电脑版左下角“免费用豆包”每日签到领取约 200 额度。

### 3. 付费订阅或“开源 Codex 外壳 + 自备 DeepSeek API”（自动化批量首选）

- 个人付费一体化方案：若平时已有付费预算，可直接考虑订阅 OpenAI 官方的 Codex（同时提供桌面图形客户端与命令行工具）。
- 高性价比自动化组合（开源 Codex CLI 外壳 + DeepSeek API）：OpenAI 的命令行智能体外壳 `@openai/codex` 本身是开源软件（备选也可使用 Claude Code 外壳，但本仓库优先推荐并已内置 Codex 批量驱动脚本）。由于 DeepSeek 官方接口已原生兼容 Codex 所需的 Responses 协议，只需三步即可把你的 DeepSeek `API Key` 装进 Codex 外壳中：

  1. 安装 Node.js（18 及以上版本）后全局安装开源 Codex CLI，并首次运行一次以生成配置目录：

     ```bash
     npm install -g @openai/codex
     codex --version
     ```

  2. 运行 [DeepSeek 官方接入 Codex 指南](https://api-docs.deepseek.com/quick_start/agent_integrations/codex/) 提供的一键配置脚本，按终端菜单提示填入你的 DeepSeek `API Key`（以 `sk-` 开头）：

     ```bash
     # macOS / Linux 终端执行：
     bash <(curl -fsSL https://cdn.deepseek.com/api-docs/codex-deepseek-setup-en.sh)

     # Windows PowerShell 执行：
     irm https://cdn.deepseek.com/api-docs/codex-deepseek-setup-en.ps1 | iex
     ```

  3. 验证非交互命令行调用是否畅通：

     ```bash
     codex exec --skip-git-repo-check "请回复连接成功"
     ```

     验证通过后，后续即可直接使用本仓库的 `agent_lab/run_codex_batch.py` 自动运行整个代码优化基准。

## 四、亲手体验裸 API 调用与提示工程基础

为了直观体会“裸 API 调用”与“工具循环外壳”在代码层面的区别，建议花 10 分钟运行一下 `part1_basics/` 中的两个百行以内示例脚本：

```bash
pip install -r requirements.txt
cp config_template.py config.py   # 在 config.py 中填入你的 DeepSeek 或课题组门户 API_KEY
python3 part1_basics/01_hello_api.py
python3 part1_basics/02_structured_and_tools.py
```

- `01_hello_api.py` 演示基础的单次裸 API 请求，并打印输入与输出 Token 用量及前缀缓存命中情况（多轮对话前缀不变时，服务端会自动命中缓存并显著降低计费）。
- `02_structured_and_tools.py` 通过不到 100 行代码拆解了 Agent 外壳的工作原理：向裸 API 传入本地工具定义（`tools`），在循环中替模型执行本地函数并将输出结果追加回对话，裸接口便具备了自主读取热点与源码的能力。

在此基础上，无论手动向 Qoder 提问还是编写自动化脚本，针对代码性能优化设计提示词（Prompt）只需抓住三个要点：

1. 锁定等价边界：明确要求保持公开函数名、参数签名、返回值格式、异常抛出条件以及可变状态下的缓存失效逻辑不变，每次修改后必须运行单元测试校验。
2. 提供动态热点证据：包含十余个函数的模块中，仅凭静态通读源码容易误改只执行一次的初始化或格式化逻辑。要求智能体先运行性能剖析（`cProfile`），依据实测耗时排行定位瓶颈。
3. 沿调用链上下游追踪根因：某个底层函数累计耗时最高，往往源于上游调用方（Caller）在循环内部成千上万次重复调用它或重复解析相同参数。提示智能体同时检查“上游调用方 — 热点函数 — 下游被调函数”，更容易发现大幅加速的跨函数协同改法。
