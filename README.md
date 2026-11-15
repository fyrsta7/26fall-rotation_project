# 软件优化智能体设计（2026 秋季图灵班科研轮转 · 第一周）

本仓库是北京大学熊英飞老师课题组 2026 年秋季图灵班统一科研轮转计划中第一周“软件优化智能体设计”（负责人：赵雨薇，`zhaoyuwei@stu.pku.edu.cn`）的配套实践仓库，同时包含第六周自选拓展方向的进阶课题说明。

第一周内容默认同学们此前没有接触过大模型接口或编程智能体。遇到环境配置、额度开通或实验问题时，欢迎随时通过微信或邮件联系负责人，也推荐借助编程智能体排查日常报错。

## 一、轮转安排与一周工作量一览（必做与拓展）

按照课题组统一安排（每周阅读 1–2 篇论文或等量学习资料，完成一个轻量小练习，并在下一周进行 10 分钟 PPT 汇报），本方向内容分为第一周必做任务与第六周可选拓展，第一周总投入约 6.5 至 8 小时：

| 阶段 | 模块 | 内容与交付要求 | 预计耗时 |
| --- | --- | --- | --- |
| 第一周（必做） | 1. 认识并配置 API 与 Agent | 阅读入门指南，分清裸大模型 `API Key` 与编程智能体 `Agent` 外壳的区别，完成工具安装与两个基础示例验证 | 约 45 分钟 |
| 第一周（必做） | 2. 文献脉络与论文精读 | 阅读四阶段发展脉络综述，从推荐清单中精读 1–2 篇代表性论文（1 篇经典方法 + 1 篇近期真实仓库工作） | 3–4 小时 |
| 第一周（必做） | 3. 渐进式优化小练习 | 在轻量基准 `PyOpt-Lite`（8 道任务）上：先使用 Qoder 手动对话尝试 2–3 个例子摸索有效提示词，再通过自动化脚本批量运行全部任务对比整体收益 | 1.5–2 小时 |
| 第二周初（必做） | 4. 10 分钟 PPT 汇报 | 制作 PPT 进行 10 分钟汇报，包含论文阅读总结、手动与批量实验的对比结果及典型案例分析 | 约 1.5 小时 |
| 第六周（可选拓展） | 5. 进阶课题探索 | 若最后一周自选本方向，可基于公开外部数据集（GSO / SWE-Perf、PIE / EffiBench-X 等）从三个课题中任选其一深入研究 | 第六周整周 |

## 二、仓库目录导航

```text
26fall-rotation_project/
├── config_template.py               # 裸 API 配置模板（供 part1_basics 与纯 Python 备选脚本使用）
├── requirements.txt                 # Python 依赖（仅需 openai>=1.40.0，评测器仅依赖 Python 标准库）
├── docs/
│   ├── 01_api_and_agent_guide.md    # 零基础必读：API Key 与 Agent 概念、Qoder 与 Codex+DeepSeek 安装指南
│   ├── 02_literature_roadmap.md     # 零基础必读：代码优化四阶段演进脉络与 1–2 篇论文精读指南
│   └── 03_week6_extensions.md       # 第六周可选：基于公开外部基准的三个进阶拓展课题
├── part1_basics/
│   ├── 01_hello_api.py              # 裸 API 单次调用与前缀缓存命中统计示例
│   └── 02_structured_and_tools.py   # 不到 100 行代码拆解 Agent 外壳如何通过循环调用工具
├── benchmark/                       # PyOpt-Lite：8 道标准库 Python 多函数性能基准任务
│   ├── tasks.json                   # 任务清单、入口函数与核心性能反模式说明
│   ├── tasks/                       # 待优化源码 target.py、性能负载 workload.py 与单元测试 test_target.py
│   └── reference_patches/           # 供评测器计算专家达成率的参考实现（实验期间请勿读取或喂给模型）
└── agent_lab/                       # 第一周代码优化实验工作台
    ├── prompts/                     # 提示词模板（含基础提示 naive_prompt.txt 与引导式提示 guided_agent_prompt.txt）
    ├── run_codex_batch.py           # 批量脚本：准备手动工作区，或调用开源 Codex CLI 外壳 + DeepSeek API 自动跑批
    ├── profiler_tools.py            # 辅助诊断工具：提取 cProfile 热点排行与 AST 静态上下游调用链关系
    ├── baseline_direct.py           # 备选纯 Python 脚本：单轮裸 API 直接生成基线
    ├── agent_starter.py             # 备选纯 Python 脚本：无需安装 Node/Codex 的轻量多轮反馈智能体
    └── evaluate.py                  # 统一评测脚本（输出 Pass@1、GeoMean 加速比、Opt@1.2x、Opt_Ref）
```

## 三、基础准备：区分 API Key 与 Agent，并完成论文阅读

### 1. 理解并准备 API Key 与 Agent（详见 [docs/01_api_and_agent_guide.md](docs/01_api_and_agent_guide.md)）

初次接触大模型工具时，请先区分两个基础概念：

- `API Key`（裸的大模型调用接口）：大模型本身只有基础的“输入一段文字、输出一段文字”能力，无法自行打开本地文件或运行测试。获取途径有两种：一是联系负责人开通[课题组大模型门户](https://llm.xmcp.ltd/)额度；二是自行前往 [DeepSeek 开放平台](https://platform.deepseek.com/) 充值 10 元人民币（运行完第一周全部自动化实验通常仅需 0.5–2 元；进阶也可尝试折扣期单价接近 DeepSeek 的阿里云百炼 `qwen4-max-preview`、腾讯混元 `Hy4` 或 Google `Gemini 4`；个人请勿直接注册充值 Claude，容易触发封号）。
- `Agent`（给 API 套上一层读写文件与执行命令外壳的编程智能体）：外壳程序赋予了大模型浏览目录、修改代码文件以及在终端运行测试的能力。常用渠道有三类：
  1. 学校免费提供（手动交互首选）：北大正版授权 Qoder，直接查看[北大计算中心 Qoder 开通说明](https://cc.pku.edu.cn/notice/859.html)完成授权并前往 [Qoder 客户端下载页](https://qoder.cn/download) 安装，每月免费享有 3,000 Credits；
  2. 其他免费桌面客户端：腾讯 WorkBuddy（每日签到送 100–200 积分，内置混元 `Hy4` 免费或优惠档）、阿里千问办公或豆包工作桌面端；
  3. 付费订阅或“开源外壳 + 自备 API”（自动化批量首选）：个人付费可考虑 OpenAI 官方的 Codex；免费外壳则推荐安装开源的 OpenAI Codex CLI（`npm install -g @openai/codex`），再按 [DeepSeek 接入 Codex 官方指南](https://api-docs.deepseek.com/quick_start/agent_integrations/codex/) 运行一键配置脚本挂载你自己的 DeepSeek `API Key`（外层复用成熟的 Codex 外壳读写文件与执行测试，底层仅消耗几毛钱的 DeepSeek 接口额度）。

克隆本仓库后，可先运行 `part1_basics/` 中的两个简短示例了解底层调用机制：

```bash
git clone https://github.com/fyrsta7/26fall-rotation_project.git
cd 26fall-rotation_project
pip install -r requirements.txt
cp config_template.py config.py   # 填入你的 DeepSeek 或课题组门户 API_KEY
python3 part1_basics/01_hello_api.py
python3 part1_basics/02_structured_and_tools.py
```

### 2. 梳理代码优化发展历程并精读 1–2 篇论文（详见 [docs/02_literature_roadmap.md](docs/02_literature_roadmap.md)）

阅读 `docs/02_literature_roadmap.md` 了解领域四个演进阶段（编译器手工规则 → 单函数进化搜索 → 真实仓库知识引导与跨函数优化 → 长程探索与自进化智能体），并按以下搭配精读 1–2 篇论文：

- 第 1 篇（经典搜索或策略库方法，二选一精读）：[SBLLM](https://arxiv.org/abs/2408.12159)（ICSE 2025，单函数算法题上的“检索示例 + 耗时反馈 + 进化搜索”代表作，直观易读）或课题组论文 [SemOpt](https://arxiv.org/abs/2510.16384)（ACM TOSEM 2026，从开源历史提交聚类提炼优化策略库引导大模型）。
- 第 2 篇（近年真实仓库新进展，二选一阅读）：[GSO](https://arxiv.org/abs/2505.23671)（NeurIPS 2025，真实软件仓库性能优化基准与智能体瓶颈分析）或 [PEACE](https://arxiv.org/abs/2510.17142)（ASE 2025，真实 Python 项目跨函数依赖分析与协同编辑）。

## 四、第一周必做小练习：从手动对话摸索到自动化批量优化

### 1. 评测基准（PyOpt-Lite）与定量指标

为了让同学们在个人电脑上免安装大型容器环境就能快速获得客观可比的加速数据，本仓库提供了包含 8 道标准库 Python 多函数性能任务的轻量可执行基准 `PyOpt-Lite`（全量 8 题单元测试与多轮重复计时合计约 12 秒）：

| 任务 ID | 场景主题 | 性能反模式与诊断看点 | 参考补丁加速比 |
| --- | --- | --- | ---: |
| `task_01_log_router` | 日志分级路由匹配 | 叶子匹配函数耗时占比突出，根因是上游批量循环重复解析规则文本与编译正则 | ~8.8x |
| `task_02_graph_reach` | 依赖图传递可达性 | 批量查询重复触发图遍历；若直接在可变图实例上永久缓存而忽略增删边失效会破坏语义 | ~5.5x |
| `task_03_event_dedup` | 事件保序去重聚合 | 去重、黑名单与用户标签合并存在三处线性扫描，需在保持首次出现顺序的前提下协同替换 | ~44.0x |
| `task_04_csv_aggregator` | 账单宽表按月汇总 | 只读统计前调用了防御性深拷贝辅助函数，且日期解析需保留非法输入抛出异常的契约 | ~35.0x |
| `task_05_token_matcher` | 多词术语语料扫描 | 外层术语循环反复触发内层全文分词，需提升文档分词并按词组长度组织匹配 | ~65.0x |
| `task_06_config_overlay` | 多层配置嵌套展开 | 高频字典合并与占位符展开；引入缓存时必须在 `set_override` / `update_env` 等入口同步失效 | ~15.5x |
| `task_07_matrix_window` | 二维窗口异常检测 | 重叠矩形窗口重复求和，可改写为二维前缀和与平方前缀和（须兼容非正方形窗口） | ~23.5x |
| `task_08_json_normalizer` | 结构化载荷幂等指纹 | 递归序列化中逐字符拼接与字典二次构造（须保留 `bool` 与 `int` 区分及 `-0.0` 语义） | ~2.0x |

运行 `python3 agent_lab/evaluate.py --use-reference` 即可验证本地评测环境。评测器会自动检查单元测试与工作负载输出一致性，并输出四项指标：

- `Pass@1`（功能正确率）：通过全部单元测试且输出与原始实现完全一致的任务比例（未通过的任务有效加速比记为 `1.00x`）；
- `GeoMean Speedup`（几何平均有效加速比）：全部任务有效加速比的几何平均值；
- `Opt@1.2x`（有效优化率）：正确且实测加速比达到 `1.20x` 及以上的任务比例；
- `Opt_Ref`（参考水平达成率）：正确且实测加速比达到参考优化实现 85% 及以上的任务比例。

### 2. 第一步：手动交互探索（使用 Qoder 对话先试 2–3 道题，建立直觉）

刚开始接触时，直接编写自动化脚本既容易受阻于工程细节，也不便于观察模型实际的思考与出错过程。建议先打开 Qoder（或 WorkBuddy）图形客户端手动尝试 2–3 个具体任务（例如 `task_01_log_router` 与 `task_06_config_overlay`）：

1. 先在终端生成一份独立的手动实验副本（避免直接改动 `benchmark/tasks/` 下的原始文件，同时自动隔离参考答案）：

   ```bash
   python3 agent_lab/run_codex_batch.py --prepare-only --output-dir workspace/manual_try
   ```

2. 打开 Qoder 软件，加载子目录 `workspace/manual_try/task_01_log_router` 并新建对话：
   - 先尝试基础提问：把 `agent_lab/prompts/naive_prompt.txt` 中的简单指令输入对话（例如要求在不改变功能的前提下优化 `target.py` 的运行效率），观察它修改了哪些函数；
   - 运行评测查看结果：

     ```bash
     python3 agent_lab/evaluate.py --candidate-dir workspace/manual_try --task task_01_log_router
     ```

   - 再尝试补充诊断信息与执行步骤：在终端运行 `python3 agent_lab/profiler_tools.py --task task_01_log_router` 查看 `cProfile` 热点函数与上下游调用链（Caller-Callee）并贴入对话，或者参考 `agent_lab/prompts/guided_agent_prompt.txt` 要求 Qoder 先运行剖析定位造成重复开销的上游调用链、修改后自行运行单元测试与计时对比、遇到报错继续迭代修正。
3. 在 2–3 个任务上调整输入信息与提示结构，观察补充哪些关键线索（热点数据、上下游调用关系、状态失效提醒、测试命令）能够稳定提升正确率与加速倍数。

### 3. 第二步：自动化批量调用（使用开源 Codex 外壳 + DeepSeek API 批量运行）

在手动对话中摸索出一套效果稳定的提示词与工作步骤后，即可将其应用到全部 8 道基准任务上批量运行，检验哪种方法在完整数据集上的整体收益更显著。

- 方式一（推荐）：开源 Codex CLI 外壳 + 自备 DeepSeek API（或课题组门户 API）
  按照 `docs/01_api_and_agent_guide.md` 第三节配置好 `@openai/codex` 与 DeepSeek API 后，将打磨好的提示词保存为文本文件（例如 `agent_lab/prompts/my_prompt.txt`），运行批量驱动脚本 `run_codex_batch.py`。该脚本外层调用开源 Codex 外壳自动完成文件读写与终端测试，内层调用低成本的 DeepSeek API：

  ```bash
  # 对照组：使用基础提示词自动运行全部 8 道题
  python3 agent_lab/run_codex_batch.py \
    --prompt-file agent_lab/prompts/naive_prompt.txt \
    --output-dir workspace/codex_naive

  # 实验组：使用加入剖析、调用链分析与多轮验证要求后的提示词自动运行全部 8 道题
  python3 agent_lab/run_codex_batch.py \
    --prompt-file agent_lab/prompts/guided_agent_prompt.txt \
    --output-dir workspace/codex_guided

  # 输出两组方法的定量对比表
  python3 agent_lab/evaluate.py --candidate-dir workspace/codex_naive --output outputs/naive_eval.json
  python3 agent_lab/evaluate.py --candidate-dir workspace/codex_guided --output outputs/guided_eval.json
  ```

- 方式二（备选）：纯 Python 轻量脚本（无需安装 Node.js / Codex CLI）
  若本地不便安装 Node.js，也可直接运行仓库内置的纯 Python 基线与模块化智能体脚手架（读取 `config.py` 中的 `API Key`）：

  ```bash
  python3 agent_lab/baseline_direct.py --output-dir workspace/py_direct
  python3 agent_lab/agent_starter.py --use-profiler --use-call-chain --max-rounds 3 --output-dir workspace/py_agent
  python3 agent_lab/evaluate.py --candidate-dir workspace/py_direct
  python3 agent_lab/evaluate.py --candidate-dir workspace/py_agent
  ```

实验纪律提醒：无论手动对话还是自动化脚本，均不得让模型读取 `benchmark/reference_patches/` 目录下的参考答案。

## 五、下周汇报要求与第六周自选拓展

### 1. 第二周初 10 分钟 PPT 汇报建议结构

1. 文献阅读收获（约 4 分钟）：概述所读 1–2 篇论文的核心问题、技术方案（如进化搜索、策略库引导或跨函数协同编辑）与局限性。
2. 手动摸索与批量实验对比（约 4 分钟）：分享手动使用 Qoder 调试单题时观察到的现象，以及在全部 8 道题批量运行后不同方法在 `Pass@1`、`GeoMean Speedup`、`Opt@1.2x`、`Opt_Ref` 上的对比结果。
3. 典型案例复盘（约 2 分钟）：结合 1–2 个具体任务展示仅靠静态阅读代码为何容易出现定位偏差或破坏边界条件，以及引入性能剖析、上下游调用链或测试反馈后带来了哪些具体改变。

### 2. 第六周自选方向拓展预览（详见 [docs/03_week6_extensions.md](docs/03_week6_extensions.md)）

若最后一周选择回到本方向深入探索，所有拓展课题均基于完全公开的外部数据集，无需额外申领内部数据：

- 拓展方向一：在公开仓库级基准（[GSO](https://github.com/gso-bench/gso) / [SWE-Perf](https://github.com/SWE-Perf/SWE-Perf)）上探索跨文件热点定位与优化；
- 拓展方向二：基于公开算法与多语言效率数据集（[PIE](https://github.com/madaan/pie-perf) / [EffiBench-X](https://github.com/EffiBench/EffiBench-X)）探索示例检索增强（RAG）与结构化优化技能归纳；
- 拓展方向三：结合 `PyOpt-Lite` 与公开效率题集（如 [EffiBench-X](https://huggingface.co/datasets/EffiBench/effibench-x) / [COFFE](https://github.com/JohnnyPeng18/Coffe)），探索基于失败轨迹反思的自进化代码优化智能体（RSI / Meta-Agent）。
