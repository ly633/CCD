Tight-Inclusion baseline：已在本机跑通
====================================

论文与代码
----------

论文：A Large Scale Benchmark and an Inclusion-Based Algorithm for Continuous
Collision Detection，Wang 等，ACM Transactions on Graphics，2021。

论文主页：https://continuous-collision-detection.github.io/tight_inclusion/
上游仓库：https://github.com/Continuous-Collision-Detection/Tight-Inclusion

本地目录：D:\ly\DGP-Autoreasearch
本地分支：baseline/tight-inclusion-v1.0.6
上游标签：v1.0.6
上游提交：7377d78162f9fdb5fe44b54b6f9c01bc6ce0885a

本分支没有修改上游 src/、app/、cmake/ 和 CMakeLists.txt。
新增内容为依赖配置、运行脚本、结果与说明。
注意：上游 v1.0.6 的 CMake 工程内部版本号仍为 1.0.4；以 Git 标签和提交为准。

已经完成的实验
--------------

运行原版 app/main.cpp 的四组官方 sample queries，保留原版统计方式。
一次预热，三次正式运行；串行执行 CCD 查询，进程固定到逻辑 CPU 0。
下表耗时是三次正式运行的各组中位数，单位为秒。

====================== ========= =========== ====== ======
数据组                 查询数    CCD 耗时    漏检   误报
====================== ========= =========== ====== ======
模拟数据 / 顶点—面      100000    0.0772803   0      0
模拟数据 / 边—边        100000    0.0810120   0      0
人工构造 / 顶点—面      3085      4.9450800   0      85
人工构造 / 边—边        4194      16.9437000  0      137
====================== ========= =========== ====== ======

每次共 207279 个查询，三次的漏检和误报数量一致。
三次“每轮 CCD 总耗时”的中位数为 22.052937 秒。
逐组中位数之和不必等于每轮总耗时的中位数。
计时由原版每查询计时器完成，不含数据文件读取；完整进程墙钟耗时另存于 JSON。

这是官方样例集复现，不是论文约 6000 万查询的全量实验。
样例包含 Boolean ground truth。本次未测精确 TOI 误差，也未新增最小分离距离测试。
零漏检表示通过此样例集，不能替代对算法保守性的证明。
222 个误报是原版在以下固定设置上的实测结果，保留作后续比较基准。

固定参数
--------

* double precision
* BREADTH_FIRST_SEARCH
* tolerance = 1e-6
* minimum_separation = 0
* max_iterations = 1000000
* t_max = 1
* err = (-1, -1, -1)，由原库计算误差界
* no_zero_toi = false
* 队列大小限制关闭，额外内部计时关闭

环境
----

* Windows 11，10.0.26200
* Intel Core Ultra 7 265KF，20 核 / 20 逻辑处理器，约 64 GB 内存
* Visual Studio 2022 Build Tools 17.14.33
* MSVC 19.44.35227.0，Windows SDK 10.0.26100.0
* CMake 4.3.3，Python 3.13.9（脚本要求 Python >= 3.11）
* Release，/O2 /Ob2 /DNDEBUG，AVX2，原默认浮点模式，未开启 fast-math
* Eigen 3.4.0，GMP 6.3.0，spdlog 1.11.0，CLI11 2.3.2，JSON 3.11.2

使用本机已有的 Eigen 和 GMP，没有安装或修改全局软件环境。
GMP DLL 已复制到可执行文件同目录；数据加载仍使用官方 GMP 读取器。

重跑
----

在 PowerShell 中执行::

    Set-Location D:\ly\DGP-Autoreasearch
    .\scripts\setup-baseline.ps1
    python scripts\run-baseline.py

运行脚本默认创建带时间戳的新结果目录，不覆盖已保存的实验。
也可指定新目录::

    python scripts\run-baseline.py --output baseline-results/my-rerun --repeats 3 --warmups 1 --cpu 0

设置脚本支持 -GmpPrefix、-EigenConfigDir 和 -BuildDirectory 参数。
更换机器时需具备 VS 2022 C++ 编译工具、CMake、Git、Python、Eigen 3.4.0、GMP，
并传入本机的依赖路径。首次下载依赖需要网络。

直接运行原版程序也可以，但不会固定 CPU 或生成结果 JSON::

    .\build-baseline\app\Release\Tight_Inclusion_bin.exe --no-pbar

可执行文件：build-baseline/app/Release/Tight_Inclusion_bin.exe

为解决本次复现中的环境问题，设置脚本做了以下构建适配：

* 使用 CMake 4 的旧策略兼容参数 CMAKE_POLICY_VERSION_MINIMUM=3.5。
* MSVC 加入 /utf-8，保留 Windows 定义、异常处理等默认参数。
* Git 仅获取依赖指定的提交，避免 CPM 全分支克隆在当前网络停滞。
* 样例从官方 codeload 下载固定提交的归档，并检查 SHA-256。
* 通过独立 CMake hook 连接已固定的依赖和数据，原始算法及示例代码不变。

固定样例提交：4d6cce33477d8d5c666c31c8ea23e1aea97be371
样例归档 SHA-256：1bab4462d6d42148bfadcca8a08c2dfb1d2de0d0e9f2072ac71ea8f6c37ba891

结果文件
--------

* baseline-results/20261008-msvc/results.json：三次运行、预热、汇总、参数及可执行文件哈希。
* baseline-results/20261008-msvc/environment.json：硬件、编译器、依赖和编译设置。
* baseline-results/20261008-msvc/dataset-manifest.json：每个输入 CSV 的查询数和 SHA-256。
* baseline-results/20261008-msvc/run-1.log 至 run-3.log：原版程序的原始输出。
* baseline-results/20261008-msvc/warmup-1.log：预热输出。
* baseline-results/setup/configure.log 与 build.log：成功构建的记录。

保留 baseline 分支用于对照。后续修改应新建优化分支，使用相同硬件、输入和参数。
当前 run-baseline.py 会拒绝修改过的核心源码，以防误把优化版本记录成原版 baseline；
建立优化评测时应显式扩展此检查，并同时评估 TOI 和实际输出容差。
