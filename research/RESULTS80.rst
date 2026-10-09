Tight-Inclusion CCD：80% 目标阶段报告
===================================

当前结论
--------

80% 耗时降低目标尚未达到。目前最佳有效版本为 C07，源码提交
0752bc0127b3c2d6e0ed9aa598f01f2102f88a1b。同期三轮交替全量对照的
CCD 核心耗时中位数从 72.726807293 秒降至 42.484861801 秒，
降低 41.58294%，加速比 1.711829。历史 74.37439 秒未用作分母。

已完成七个有效候选实验 C01--C07。C08 编译成功，但定向测试进程
三次被 Windows Smart App Control 拒绝创建（WinError 4551），
尚无运行结果，不计入有效实验。20 个候选的停止条件尚未达到。
本报告交付当前最佳结果，并记录继续实验所遇到的环境阻塞；
不宣称研究目标完成。研究工作树当前源码是待评测 C08，不能将其
当作已验证 C07。原 baseline 工作树保持干净，数据和结果未修改。

全量同期对照
------------

实际顺序为 reference-1、candidate-1、reference-2、candidate-2、
reference-3、candidate-3。每轮均为全部 59,387,883 条查询。

.. list-table:: 每轮 CCD 核心秒数
   :header-rows: 1

   * - 轮次
     - 原版
     - C07
   * - 1
     - 72.553636823
     - 42.346088013
   * - 2
     - 72.726807293
     - 42.559761688
   * - 3
     - 73.126611941
     - 42.484861801
   * - 中位数
     - 72.726807293
     - 42.484861801

先对每轮四组 CCD 耗时求和，再取三个总数的中位数。数据加载、
缓存转换、文件读写、输出比较、哈希计算均不计入指标。硬件、
编译配置、单线程与逻辑 CPU 0 亲和性一致；double、BFS、
tolerance=1e-6、max_iterations=1000000、minimum_separation=0、
t_max=1、no_zero_toi=false。使用原版自动数值误差估计。

.. list-table:: 每轮结果一致的正确性统计
   :header-rows: 1

   * - 组
     - 查询数
     - 原版 FP
     - C07 FP
     - C07 FN
   * - 仿真点—面
     - 17,959,962
     - 2
     - 2
     - 0
   * - 仿真边—边
     - 41,372,584
     - 17
     - 17
     - 0
   * - 人工点—面
     - 21,208
     - 90
     - 67
     - 0
   * - 人工边—边
     - 34,129
     - 203
     - 161
     - 0

除 65 个原版误报被正确剔除以外，全部返回 Boolean、TOI 和
output_tolerance 均与原版逐位一致。剔除误报返回 no-hit、正无穷
TOI 和输入 tolerance；任何其他输出差异都会使评测失败。
这验证了原版碰撞时间行为的保留。数据集没有精确 TOI 真值，
因此不声称做了独立的绝对 TOI 误差测量。

保守性依据
----------

C01--C06 复用相同已舍入子表达式、移前原样初始区间判定、
用可精确表示的二进制倒数替换二进制分母除法，以及内联完全
相同的整数运算；保留浮点运算次序、误差界和队列比较次序。
详见 NUMERICS.rst 与 CONTINUED_NUMERICS.rst。

C07 新增 minimum_separation=0 时的 swept AABB 剔除。线性运动
顶点坐标位于其两端点坐标闭区间中；边和三角形上的点为顶点
凸组合，因此也在所有端点的坐标范围内。任意坐标轴上两个
范围严格分离即可证明整个时间区间没有碰撞。min/max 仅选择
输入 double，严格比较不引入数值运算舍入；相等边界不剔除。
公共单调 rational-to-double 转换也不能将相交区间变为严格分离。
未剔除查询使用原求解器，保留其保守误差界与 TOI。这是独立
几何必要条件，不依赖本次测试恰好零漏检。

候选记录
--------

子集在实现候选前固定为 546,337 条；全部人工样例、全部仿真
真碰撞及仿真 CSV 每 128 条抽样。它偏重困难案例，不将子集
耗时直接解释为全量收益。各次筛选并非同期交替对照，较小的
筛选差异只用于研究选择；最终收益仅使用上述交替全量实验。

* C01，31d8312：复用时间插值；子集 28.513 秒，完整首次筛选
  62.640 秒，未达到早期目标；保留为后续候选组成部分。
* C02，aa821e0：先做相同初始盒判定，避免无效 setup；早期三轮
  全量中位数 52.472 秒，对同期原版降低 27.73%。原报告 RESULTS.rst
  单独保留，它完成的是早期 20% 目标。
* C03，a01babc：精确二进制倒数，子集 25.792708 秒，通过逐位比较。
* C04，45b9e2d：复用空间插值，子集 25.352778 秒，通过逐位比较。
* C05，c6d315d：初始盒固定 dyadic 数组，子集 24.737209 秒；
  三轮全量中位数 45.378288 秒，同期原版 72.107861 秒，降低
  37.07%。后被 C07 取代。
* C06，fac3198：内联精确整数比较，子集 24.415937 秒，通过逐位
  比较。最初遭 WinError 4551，后同文件同路径重试成功；系统
  安全策略未变更。失败与成功记录均保留。
* C07，0752bc0：保守 swept AABB 剔除，子集 22.109648 秒；
  单轮全量筛选 42.226735 秒；三轮最终全量结果见上表。
* C08，285bd40：向外舍入区间 Bernstein 共面性证书。仅已编译，
  三次定向测试进程创建被拒，无测试耗时或正确性结论，不计数。

C03--C06 逐步保留为下一候选的父版本；对应数值等价检查和固定
子集均通过，但单次子集的小幅改善不构成独立显著性结论。
详细假设、参数、版本、日志和失败原因在 ../research-results/。

交付与复现
----------

当前最佳源码：../research-results/best-c07-source.zip（src/ 目录），
相对原版的核心补丁：../research-results/best-c07-core.patch。
二者对应 C07 提交；zip 不包含依赖、构建产物或生成 config.hpp。
精确已测二进制和完整源码快照在 ../research-results/runs/c07-subset/，
本机缓存、答案与二进制保留于磁盘，未将这些大文件纳入 Git。
JSON、日志、补丁、清单和候选提交均已版本化。

在本研究目录使用已有缓存及冻结 C07 二进制重跑交替全量测试，
选择新的 prefix，已有输出目录不会被覆盖::

    python research/research.py paired --prefix c07-reproduction-01 --candidate-snapshot research-results/runs/c07-subset --allow-fp-removal --target-reduction 0.80

只复算已有结果与约束，不启动 CCD::

    python research/research.py summarize --prefix phase80-c07 --target-reduction 0.80

该命令应报告 all_correct=true、target_passed=false。要从源码重建，
在单独的复现目录检出完整 C07 提交 0752bc0，使用相同 CMake 配置；
在其 research/research.py init 后配置 TIGHT_INCLUSION_RESEARCH=ON、
double、Release，构建 research_reference / research_candidate /
research_equivalence。不要覆盖当前被系统拒绝的 C08 二进制。
本机精确配置存于 runs/c07-subset/CMakeCache.txt，全部构建参数
同时记入 results.json。缓存可由 pinned GMP 读取器和 prepare
--workers 8 重建；原始数据只读，源与缓存 SHA256 清单均保留。

对照二进制 SHA256：
dfa57741e962310f2be44ebb4fcf170ddc1c0303b770eb6719c846f6dbecfe64。
C07 二进制 SHA256：
372609ea15766ef34956ba096b699f99d9e36814946d88c4296629cc89b97734。
每个版本三次最终运行使用同一哈希；核验在 phase80-c07-delivery-check.json。

阻塞与后续入口
--------------

C08 错误、原始哈希和三次尝试见 c08-experiment.json，系统证据见
c08-code-integrity-events.json（事件 3077/3033/3118）。未修改
Smart App Control、签名信任或安全策略，也未移动或改写拒绝的
文件来绕过拦截。C08 尚不能作为有效交付版本。

若系统恢复合法执行，原文件原路径的可复现继续命令为::

    python research/experiment.py --resume --id C08 --parent C07 --allow-fp-removal --hypothesis "Resume exact unchanged C08 binaries after execution restriction resolves"

resume 首先检查已保存二进制哈希；不得将重新构建的代码冒充
同一次重试。后续假设与未执行工作见 NEXT_STEPS.rst。

Execution recheck: 2026-10-09 15:15 UTC
-------------------------------------

The first goal continuation verified the same binary hashes and retried C08
at its original path. Attempt 4 still failed before process creation with
WinError 4551. New CodeIntegrity events 3077/3033 confirm the same signing
policy block; policy state remains 1 and the executable is unsigned. There
is no live benchmark process to wait on. This is the second consecutive
goal turn with this blocker, not four effective candidate experiments.
Evidence: ../research-results/c08-continuation-1-environment.json and
../research-results/blocker-audit.json. The 80% goal remains incomplete.
