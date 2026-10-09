Tight-Inclusion baseline：官方公开全量数据已跑通
================================================

论文与代码
----------

论文：A Large Scale Benchmark and an Inclusion-Based Algorithm for Continuous
Collision Detection，Wang 等，ACM Transactions on Graphics，2021。

论文主页：https://continuous-collision-detection.github.io/tight_inclusion/
上游仓库：https://github.com/Continuous-Collision-Detection/Tight-Inclusion

本地目录：D:\ly\DGP-Autoreasearch\Tight-Inclusion
本地分支：baseline/tight-inclusion-v1.0.6
上游标签：v1.0.6
上游提交：7377d78162f9fdb5fe44b54b6f9c01bc6ce0885a

本分支没有修改上游 src/、app/、cmake/ 和 CMakeLists.txt。
新增内容为依赖配置、运行脚本、结果与说明。
注意：上游 v1.0.6 的 CMake 工程内部版本号仍为 1.0.4；以 Git 标签和提交为准。

样例实验（历史记录）
--------------------

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

    Set-Location D:\ly\DGP-Autoreasearch\Tight-Inclusion
    .\scripts\setup-baseline.ps1
    python scripts\run-baseline.py

运行脚本默认创建带时间戳的新结果目录，不覆盖已保存的实验。
也可指定新目录::

    python scripts\run-baseline.py --output baseline-results/my-rerun --repeats 3 --warmups 1 --cpu 0

设置脚本支持 -GmpPrefix、-EigenConfigDir、-BuildDirectory、-LogDirectory 和 -DataDirectory 参数。
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

目录迁移
--------

仓库已移动至 D:\ly\DGP-Autoreasearch\Tight-Inclusion，父目录仅用于容纳各研究仓库。
Git 历史、baseline 分支、依赖、数据和原始实验结果均随仓库保留。
历史 JSON 和日志中的旧绝对路径记录的是当时实际运行位置，不改写历史记录。
原构建目录保留为 build-baseline-before-relocation；其 CMake 缓存含旧路径，
仅作历史留存。日常使用重新生成的 build-baseline。
迁移后构建日志单独保存于 baseline-results/relocation-setup，验证结果保存于
baseline-results/relocation-check。

保留 baseline 分支用于对照。后续修改应新建优化分支，使用相同硬件、输入和参数。
当前 run-baseline.py 会拒绝修改过的核心源码，以防误把优化版本记录成原版 baseline；
建立优化评测时应显式扩展此检查，并同时评估 TOI 和实际输出容差。

完整官方数据基线
----------------

当前全量任务目录：baseline-results/full-2020-20261009-retry。
已于 2026-10-09 12:30:48（北京时间）完成，status=complete，退出码为 0。
官方五个数据包的全部 5203 个 CSV 共包含 59387883 条查询，约 49.29 GB。
一次预热和三次正式运行均覆盖完整数据；每轮 0 漏检、312 个误报，各轮计数一致。

以下耗时为三次正式运行中各组单次查询平均耗时的中位数：

====================== ============ =============== ====== ======
数据组                 查询数       每查询耗时/微秒 漏检   误报
====================== ============ =============== ====== ======
仿真 / 顶点—面         17959962     0.689177        0      2
仿真 / 边—边           41372584     0.701970        0      17
人工 / 顶点—面         21208        384.271030      0      90
人工 / 边—边           34129        729.432447      0      203
====================== ============ =============== ====== ======

三次每轮 CCD 总耗时分别为 74.93802、73.51284、74.37439 秒，中位数为 74.37439 秒。
计入数据读取和有理数解析后，每轮进程总耗时的中位数为 1028.19 秒（约 17.14 分钟）。
一次预热加三次正式运行共用 4077.66 秒（约 67.96 分钟），不含下载、解压和构建。
本次统计仍只验证碰撞 Boolean 判定；没有测量精确碰撞时间误差。
2026-10-09 结果复核：四轮原始日志与 JSON 一致，清单哈希及程序哈希一致，
五个归档通过 gzip CRC，5203 个输入文件均存在且大小符合清单，上游核心源码无修改。

以该目录的 status.json 为实时状态来源；仅 status=complete 表示全部运行完成。
任务流程为：下载与解压 -> 完整性校验 -> 构建 -> 一次预热和三次正式运行。
任一步骤失败会写入 status=failed 和错误原因，不会将部分结果标记为全量成功。

2026-10-08 启动的任务在当天 23:08（北京时间）于下载阶段退出，尚未开始全量计算；
失败记录保留于 baseline-results/full-2020-20261008。原下载进程只返回退出码 1，
其详细输出没有独立落盘，因此不能从现有记录确定最初的网络异常类型。
2026-10-09 已确认服务器忽略 HTTP Range 请求，并修复重试从头覆盖已有进度的问题：
现在先逐字节校验已保存前缀，只追加新增内容，连接中断时保留已有进度。
该路径仍需从服务器重新传输前缀，不能误称为服务器支持断点续传。
修复通过六项中断与续传回归检查；新任务由后台主进程启动下载子进程，
下载输出单独保存于 download.log，并记录各文件的尝试次数和错误原因。

数据来自论文主页链接的 NYU 原始 2020 年归档：

* https://archive.nyu.edu/handle/2451/61519：人工构造数据。
* https://archive.nyu.edu/handle/2451/61520：chain、cow-heads、golf-ball、mat-twist 四个仿真包。

五个压缩包合计 3366060873 字节；保存于 .cache/downloads/full-ccd-2020。
解压后的 CSV 位于 external/baseline/Full-CCD-2020。
下载验证服务端文件长度并记录 SHA-256；任务读取 gzip 到 EOF 检查 CRC；
解压时为每个 CSV 记录 SHA-256、字节数与查询数，正式运行前复核文件清单和大小。
构建使用 build-baseline-full；算法源代码和 app/main.cpp 没有修改，
仅将原版程序编译时的数据目录指向完整数据目录。
正式运行沿用 double、BFS、tolerance=1e-6、max_iterations=1e6、minimum_separation=0，
单线程并固定逻辑 CPU 0。耗时仍是原版每查询计时器统计，不包含 CSV 解析。

需注意：公开原始归档的人工构造数据实际包含 21208 个点—面查询和 34129 个边—边查询，
与论文 Table 1 标注的约 12K / 15K 不同。这里运行归档中的全部查询，不为匹配表格而删减。
2026-10-08 的人工数据预检查已完成：点—面 0 漏检 / 90 误报，边—边 0 漏检 / 203 误报。
预检查记录位于 baseline-results/full-2020-handcrafted-preflight，不能替代全量正式结果。

重新启动一次完整任务（必须使用新的输出目录）::

    python scripts/run-full-baseline.py --output baseline-results/full-2020-new-run --warmups 1 --repeats 3

数据与环境就绪后，仅重跑基准::

    python scripts/run-baseline.py --dataset full-2020 --build-dir build-baseline-full --output baseline-results/full-2020-rerun --warmups 1 --repeats 3 --cpu 0

完成后的任务目录包含 results.json、dataset-manifest.json、dataset-provenance.json、
archive-validation.json、environment.json、原始运行日志和构建日志。
results.json 会在每一轮运行后保存检查点；判断最终成功还需查看 status.json。
