Tight-Inclusion CCD 自动优化研究结果
===================================

2026-10-09：达到目标。最佳候选 C02 的全量 CCD 核心耗时中位数为
52.472144881 秒，同期原版为 72.602181521 秒，降低 27.72649%，
加速比 1.383632815×。共评测 2 个候选，按“达到目标且全量验证通过”停止。
历史 74.37439 秒没有作为加速比的分母。

最终对照实验
------------

按原版、C02、原版、C02、原版、C02 顺序串行执行，每轮全部
59,387,883 条查询。下表为四组 CCD 计算耗时之和，单位秒。

=========== ============= =============
轮次        原版          C02
=========== ============= =============
1           72.500458367  52.372528594
2           72.659458159  52.472144881
3           72.602181521  52.597744083
中位数      72.602181521  52.472144881
=========== ============= =============

统计来源：research-results/final-c02-summary.json；每轮原始输出、
参数、源码散列、程序散列、命令和壁钟时间位于
research-results/runs/final-c02-{reference,candidate}-{1,2,3}/。
性能指标不是壁钟时间，也没有把数据读取或解析加速算入成果。

正确性与精度
------------

================ ============ ========== ========== ==============
测试组           每轮查询数   原版误报   C02 误报   两版各轮漏检
================ ============ ========== ========== ==============
仿真点—面        17,959,962    2          2          0
仿真边—边        41,372,584    17         17         0
人工点—面        21,208        90         90         0
人工边—边        34,129        203        203        0
总计             59,387,883    312        312        0
================ ============ ========== ========== ==============

三轮候选均逐查询比较完整的 24 字节输出记录：碰撞布尔值、TOI、
output_tolerance，与原版差异数全部为 0，包括不碰撞时的 infinity。
这些不是仅凭摘要散列推断的一致性；程序实际逐条执行 memcmp。
还进行了固定种子下 320 万个角点输出的逐位对照，覆盖不同二进制
区间、抵消、正负零、次正规数和大数值。

数据只有布尔真值，没有精确接触时间真值。本研究证明并验证的是
保留原版的 TOI 输出与精度，没有声称独立测得绝对 TOI 误差。
输入 1e-6 是原算法的距离容差，不应误写成绝对时间误差上限。

最佳版本的修改与保守性
----------------------

最佳核心代码提交：aa821e07e003a435885f12d929b947a5d0dcdf51。
工作分支：research/ccd-autoresearch；当前 src/ 中保留最佳版本。
最佳评测程序为 build-autoresearch-sample/research/Release/research_candidate.exe，
三轮确认目录中也各保存了一份实际运行的程序及其 SHA-256。

* C01：同一盒的四个角点拥有相同时间参数，只计算一次对应的时间
  插值，复用同一个 double 结果。保持减、乘、除、加顺序及角点顺序；
  对任意数组的原 function_ee/function_vf 接口保持原样。
* C02：在计算细分容差、建立搜索队列之前，调用原 BFS 使用的同一
  初始 [0,1]^3 盒判定。若排除，返回原搜索必然返回的 false、infinity、
  输入容差；若未排除，继续原搜索，包括重新进行原初始判定。

C01 不增加相对原操作图的舍入误差，沿用原版误差过滤界；C02 的
拒绝必然等同于原 BFS 首轮的拒绝。两项修改均保留原误差常数、
误差尺度、所有细分和终止条件、max_iterations 回退与搜索队列顺序。
完整的操作等价证明及适用条件见 research/NUMERICS.rst，
不以零漏检测试代替保守性论证。

环境与计时控制
--------------

* 同一台 Intel Core Ultra 7 265KF / Windows 11 10.0.26200。
* 单计算线程，固定逻辑 CPU 0；OMP/MKL/OpenBLAS 线程设置为 1。
* MSVC 19.44.35227.0，Release /O2 /Ob2 /DNDEBUG，CCD 库 /arch:AVX2，
  默认 precise 浮点设置。核对了两版和原 baseline 的实际项目配置。
* double、BFS、tolerance=1e-6、max_iterations=1000000、
  minimum_separation=0、t_max=1、err=(-1,-1,-1)、no_zero_toi=false。
* 原版核心的 19 个文件从 v1.0.6 提取并逐字节核验，提交为
  7377d78162f9fdb5fe44b54b6f9c01bc6ce0885a。原版与候选链接同一个
  评测入口的分别编译版本，使用完全相同的文件和查询顺序。
* 沿用原版逐查询 Timer，开始于 API 参数转换之前，结束于 CCD 返回之后。
  文件读取、结果检查、散列和写盘均在计时之外。

所有源 CSV 在转换前重新核验 SHA-256，再由固定版本的原版
CCD-Query-IO GMP 读取器转换为相同 double 值。缓存记录原样保存
24 个 double 和真值。8 路并行只用于计时前的数据准备，未与性能
测试重叠。最终又核验了全部 10,406 个全量及子集缓存文件的 SHA-256。
数据读取格式的变化只用于缩短实验等待时间。

全量源清单 SHA-256：
92417a5c23055344bc1c17f2e6dc9a3c126c187be735467f2dc0289f03c963fa。
完整转换清单和 provenance 见 research-results/cache/。

候选研究记录
------------

固定筛选集在候选实现前确定：546,337 条，包括全部人工案例、
所有仿真真碰撞、每个仿真 CSV 中索引 0,128,256,... 的查询。
保留了耗时较高的人工案例，不能用其速度提升代替全量提升。
带插桩的原版诊断发现包围盒判定占 37.062 秒，其中角点求值
18.017 秒；诊断总时间 62.832 秒含计时开销，未用作性能基线。

===== =========== ============ =========== ================================
版本  子集中位秒  首次全量秒   正确性      结论
===== =========== ============ =========== ================================
原版  34.712142   72.664554    通过        同期筛选对照
C01   28.513260   62.640225    逐位一致    全量仅降低 13.795%，不足 20%
C02   28.249768   53.196764    逐位一致    进入三轮交替确认，最终达到目标
===== =========== ============ =========== ================================

C01 提交为 31d8312b38fbf09c35c741912b7cd131acbd1fc8；C02 以其为父版本。
各候选的假设、版本、构建日志、结果和不采用原因见
research-results/c01-experiment.json、c02-experiment.json、
experiment-index.json 以及对应 runs/ 子目录。
未把环境预检、重复运行、性能插桩当作额外候选。

复现
----

在当前已构建且缓存完整的工作树中，使用未用过的输出前缀::

    Set-Location D:\ly\DGP-Autoreasearch\Tight-Inclusion-autoresearch
    python research/research.py paired --prefix reproduce-c02-01

该命令串行执行三组原版/C02 全量对照，校验各组正确性及逐位输出，
生成 research-results/reproduce-c02-01-summary.json。已有输出目录
不会被覆盖。若仅重新计算已保存六轮的统计::

    python research/research.py summarize --prefix final-c02

重新构建最佳核心和评测入口::

    python research/research.py init
    .\scripts\setup-baseline.ps1 -BuildDirectory build-autoresearch-sample -LogDirectory research-results/reproduce-setup -DataDirectory ..\Tight-Inclusion\external\baseline\Sample-Queries-4d6cce3
    cmake -S . -B build-autoresearch-sample -DTIGHT_INCLUSION_RESEARCH=ON
    cmake --build build-autoresearch-sample --config Release --target research_reference research_candidate research_profile research_equivalence --parallel 8
    .\build-autoresearch-sample\research\Release\research_equivalence.exe

缓存尚不存在时才运行以下准备命令；它读取原 baseline 数据，但仅
在本研究工作树写缓存，不重新下载或覆盖原始数据::

    python research/research.py prepare --workers 8

代码、JSON 清单、日志、差异和证明已保存到研究分支。体积较大的
缓存、逐查询答案及 exe 保留在本地研究目录，不写入 Git；可用上述
命令重建。原 baseline 工作树仍干净，其源码、构建、数据和历史结果
保留原状，最终核验记录见 research-results/post-validation-integrity.json。
