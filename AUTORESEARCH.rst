CCD Autoresearch 工作树
======================

工作树：D:\ly\DGP-Autoreasearch\Tight-Inclusion-autoresearch
分支：research/ccd-autoresearch
起点：497baaab37b9a080d8d0db5b84ea13f50fc507e0（完整 baseline 已验证）
研究目标：等待用户指定；尚未启动 Goal Mode / 自动研究循环。

准备状态
--------

2026-10-09 已完成独立 Release 编译，原 baseline 工作树仍保持干净。
新程序的样例运行被 Windows Smart App Control 阻止，错误为 WinError 4551。
系统 CodeIntegrity 日志事件 3077 / 3033 / 3118 确认新生成的未签名 exe
不符合当前代码完整性策略；本工作树的运行验证尚未通过，也没有开始自动研究。
诊断保存在 baseline-results/autoresearch-worktree-check/status.json 和
code-integrity-events.json。实际运行实验前需解决系统执行策略问题。
本次没有修改系统安全设置，也没有对程序拦截进行规避。

目录和数据
----------

代码、依赖副本、构建目录和新实验结果放在本工作树内。
原 baseline 工作树为 ../Tight-Inclusion，其源代码和实验结果保留作为对照。
约 49.29 GB 的完整数据不重复下载；通过明确的参数读取原数据目录：

* 样例：../Tight-Inclusion/external/baseline/Sample-Queries-4d6cce3
* 全量：../Tight-Inclusion/external/baseline/Full-CCD-2020
* 全量对照结果：baseline-results/full-2020-20261009-retry/results.json

最后一项是 Git 已保存并带到本工作树的历史结果，其中绝对路径是原实验运行位置。
共享数据只作为输入使用；不要向这些目录写入或重新运行下载脚本覆盖它们。

环境准备与检查
--------------

依赖使用与 baseline 相同的固定版本，本工作树内持有独立依赖副本和 CMake 缓存。
重建样例程序::

    .\scripts\setup-baseline.ps1 -BuildDirectory build-autoresearch-sample -LogDirectory baseline-results/autoresearch-worktree-setup -DataDirectory ..\Tight-Inclusion\external\baseline\Sample-Queries-4d6cce3

运行未改动算法的样例检查，使用新的输出目录::

    python scripts/run-baseline.py --dataset sample --build-dir build-autoresearch-sample --data-dir ../Tight-Inclusion/external/baseline/Sample-Queries-4d6cce3 --output baseline-results/autoresearch-new-check --warmups 0 --repeats 1

准备全量构建并重跑原版（不重新下载数据）::

    .\scripts\setup-baseline.ps1 -BuildDirectory build-autoresearch-full -LogDirectory baseline-results/autoresearch-full-setup -DataDirectory ..\Tight-Inclusion\external\baseline\Full-CCD-2020
    python scripts/run-baseline.py --dataset full-2020 --build-dir build-autoresearch-full --data-dir ../Tight-Inclusion/external/baseline/Full-CCD-2020 --output baseline-results/autoresearch-full-control --warmups 1 --repeats 3

当前 baseline 运行脚本只接受未修改的核心源码。目标确定后，再建立明确标识候选版本的
评测入口；不能直接绕过检查后仍把优化版本记作 baseline。

已有对照指标
------------

* 每轮全量 59387883 条查询，0 漏检、312 个误报。
* 三轮 CCD 总耗时中位数 74.37439 秒（不含数据加载和解析）。
* 单线程、逻辑 CPU 0，double、BFS、tolerance=1e-6、max_iterations=1e6、minimum_separation=0。
* 各组误报为仿真点—面 2、仿真边—边 17、人工点—面 90、人工边—边 203。
* 目前未验证精确 TOI 误差；零漏检实验不能替代保守性证明。

指定目标
--------

下一步由用户说明希望优化的指标、允许修改的范围、正确性约束和停止条件。
给定具体目标后，研究工作应限定在本工作树，并记录每轮假设、修改、结果及保留/放弃理由。
本次准备没有预设加速百分比、运行预算或自动启动研究。

OpenAI 官方 Goal Mode 科研工作流参考：
https://learn.chatgpt.com/use-cases/discover-protein-folding-architectures#run-the-search-with-goal-mode
