"""Create the seven-part CCD study summary using saved experimental evidence."""
from pathlib import Path
from html import escape
import json
import hashlib
import statistics
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, Flowable
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf/Tight-Inclusion-study-summary-20261016.pdf'
SRC=ROOT/'research/STUDY_SUMMARY_20261016.rst'
TMP=ROOT/'tmp/pdfs/study-summary-20261016'
TMP.mkdir(parents=True,exist_ok=True)
def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))
s=read('research-results/final80-c20-summary.json')
audit=read('research-results/final80-completion-audit.json')
assert s['queries_per_run']==59387883 and audit['effective_candidates']==20
ref=statistics.median(r['ccd_seconds'] for r in s['runs']['reference'])
best=statistics.median(r['ccd_seconds'] for r in s['runs']['candidate'])
for r in s['runs']['reference']+s['runs']['candidate']:
    raw=read('research-results/runs/'+r['id']+'/results.json')
    assert raw['runs'][0]['groups']==r['groups'] and raw['valid']
    assert raw['runs'][0]['ccd_seconds']==r['ccd_seconds']
assert all([g['fp'] for g in r['groups']]==[2,6,53,130] for r in s['runs']['candidate'])
assert all(g['fn']==0 for r in s['runs']['candidate'] for g in r['groups'])
pdfmetrics.registerFont(TTFont('CN','C:/Windows/Fonts/msyh.ttc'))
pdfmetrics.registerFont(TTFont('CNB','C:/Windows/Fonts/msyhbd.ttc'))
pdfmetrics.registerFont(TTFont('Math','C:/Windows/Fonts/cambria.ttc',subfontIndex=0))
pdfmetrics.registerFontFamily('CN',normal='CN',bold='CNB')
W,H=A4; CW=W-100
BLUE=colors.HexColor('#234E68'); GRAY=colors.HexColor('#53616B')
styles={
 'title':ParagraphStyle('title',fontName='CNB',fontSize=22,leading=31,spaceAfter=10),
 'h1':ParagraphStyle('h1',fontName='CNB',fontSize=16,leading=24,spaceBefore=10,spaceAfter=10,keepWithNext=True),
 'h2':ParagraphStyle('h2',fontName='CNB',fontSize=11.2,leading=17,spaceBefore=7,spaceAfter=5,keepWithNext=True),
 'body':ParagraphStyle('body',fontName='CN',fontSize=10.2,leading=17,spaceAfter=8,wordWrap='CJK'),
 'small':ParagraphStyle('small',fontName='CN',fontSize=8.5,leading=13.5,spaceAfter=7,wordWrap='CJK',textColor=GRAY),
 'cell':ParagraphStyle('cell',fontName='CN',fontSize=9,leading=14,wordWrap='CJK'),
 'center':ParagraphStyle('center',fontName='CN',fontSize=9,leading=14,wordWrap='CJK',alignment=TA_CENTER),
 'th':ParagraphStyle('th',fontName='CNB',fontSize=9,leading=14,wordWrap='CJK',alignment=TA_CENTER,textColor=colors.white),
 'math':ParagraphStyle('math',fontName='Math',fontSize=12,leading=24,alignment=TA_CENTER,spaceBefore=2,spaceAfter=8),
}
story=[]; rst=[]; eqnum=0
def p(text,style='body'):
    story.append(Paragraph(escape(text).replace('\n','<br/>'),styles[style])); rst.extend([text,''])
def h(text):
    story.append(Paragraph(escape(text),styles['h1'])); rst.extend([text,'='*max(25,len(text)*2),''])
def sub(text):
    story.append(Paragraph(escape(text),styles['h2'])); rst.extend([text,'-'*max(25,len(text)*2),''])
def page(): story.append(PageBreak())
def link(label,url):
    story.append(Paragraph(f'<link href="{escape(url,quote=True)}" color="#234E68">{escape(label)}</link>',styles['body']))
    rst.extend([f'`{label} <{url}>`_',''])
def eq(tex):
    global eqnum
    formulae=[
      'x<sub>i</sub>(t) = (1 − t)x<sub>i</sub><super>0</super> + tx<sub>i</sub><super>1</super>,　t ∈ [0, 1],　x<sub>i</sub><super>0</super>, x<sub>i</sub><super>1</super> ∈ ℝ<super>3</super>',
      'p(t) = (1 − u − v)a(t) + ub(t) + vc(t)',
      'u ≥ 0,　v ≥ 0,　u + v ≤ 1',
      '(1 − u)a(t) + ub(t) = (1 − v)c(t) + vd(t)',
      't<super>*</super> = inf {t ∈ [0, 1] | C(t)},　inf ∅ = +∞',
      'R = 1 − T<sub>new</sub> / T<sub>base</sub>',
    ]
    story.append(Paragraph(formulae[eqnum],styles['math']))
    eqnum+=1
    rst.extend(['.. math::','','    '+tex,''])
def table(headers,rows,widths):
    vals=[[Paragraph(escape(str(x)),styles['th']) for x in headers]]
    vals += [[Paragraph(escape(str(x)),styles['cell' if i==0 else 'center']) for i,x in enumerate(row)] for row in rows]
    t=Table(vals,colWidths=[CW*x/sum(widths) for x in widths],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F1F5F7')]),('GRID',(0,0),(-1,-1),.45,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.extend([t,Spacer(1,10)])
    rst.extend(['.. list-table::','   :header-rows: 1',''])
    for row in [headers]+rows:
        for i,v in enumerate(row): rst.append(('   * - ' if i==0 else '     - ')+str(v))
    rst.append('')

p('Tight-Inclusion CCD\n自动优化研究总结','title')
p('文档日期：2026 年 10 月 16 日  |  最新全量实验：2026 年 10 月 10 日','small')
p('本研究在保留正确性约束的前提下优化连续碰撞检测。完成 20 个候选后，最佳 C20 将全量核心耗时从 72.746 秒降至 32.992 秒，降低 54.65%；误报从 312 个减至 191 个，四组漏检均为 0。[E1]')
h('1. 问题描述')
p('研究线性运动几何体之间的连续碰撞检测（CCD），包括点—三角形（VF）与边—边（EE）两类查询。每条查询给定四个顶点各自的起点和终点。')
eq(r'\mathbf{x}_i(t)=(1-t)\mathbf{x}_i^0+t\mathbf{x}_i^1,\quad t\in[0,1],\quad \mathbf{x}_i^0,\mathbf{x}_i^1\in\mathbb{R}^3')
sub('点—三角形碰撞')
p('判断是否存在 t∈[0,1] 及三角形重心参数 u、v，使移动点位于移动三角形上：')
eq(r'\mathbf{p}(t)=(1-u-v)\mathbf{a}(t)+u\mathbf{b}(t)+v\mathbf{c}(t)')
eq(r'u\geq0,\quad v\geq0,\quad u+v\leq1')
sub('边—边碰撞')
p('判断是否存在 t、u、v∈[0,1]，使两条移动线段具有共同点：')
eq(r'(1-u)\mathbf{a}(t)+u\mathbf{b}(t)=(1-v)\mathbf{c}(t)+v\mathbf{d}(t)')
sub('输出与优化对象')
p('令 C(t) 表示对应的碰撞条件在时刻 t 成立，则精确的首次碰撞时间为：')
eq(r't^*=\inf\{t\in[0,1]\mid C(t)\},\qquad \inf\varnothing=+\infty')
p('实际求解器返回保守碰撞判定和 TOI 估计。保守性要求真实碰撞不能被判为无碰撞，但允许受容差与终止条件影响的误报。本研究优化批量查询的运行时间，并保持既定的保守性和精度要求。')

page(); h('2. Baseline 算法')
p('当前实际使用的 baseline 为 Tight-Inclusion v1.0.6，核心以 C++ 实现。它通过区间包围与参数域细分排除不可能包含碰撞的区域，并采用 BFS 搜索；无法可靠排除时保留保守判定。')
p('对应论文：Bolun Wang、Zachary Ferguson、Teseo Schneider、Xin Jiang、Marco Attene、Daniele Panozzo，A Large Scale Benchmark and an Inclusion-Based Algorithm for Continuous Collision Detection，ACM Transactions on Graphics，40(5)，Article 188，2021。')
link('论文与项目主页','https://continuous-collision-detection.github.io/tight_inclusion/')
link('论文全文 PDF','https://continuous-collision-detection.github.io/tight_inclusion/CCD-benchmark-paper.pdf')
link('官方代码仓库：Continuous-Collision-Detection/Tight-Inclusion','https://github.com/Continuous-Collision-Detection/Tight-Inclusion')
link('本次 baseline 版本：v1.0.6','https://github.com/Continuous-Collision-Detection/Tight-Inclusion/tree/v1.0.6')
p('现有提升均相对于这一原版实现；尚未完成与其他 CCD 算法的统一横向比较。Python 用于组织实验、汇总结果和生成报告，不是被计时的 CCD 核心。','small')
h('3. 目标')
p('以提升效率为主，同时要求检测质量不下降，并允许减少误报。设原版与候选版本的全量核心耗时中位数分别为 T_base、T_new，降耗比例定义为：')
eq(r'R=1-\frac{T_{\mathrm{new}}}{T_{\mathrm{base}}}')
p('初始目标为 R≥20%，达成后提高到 R≥80%。停止条件为达到目标且验证通过，或累计完成 20 个有效候选。当前已按候选数量上限停止。[E2]')
sub('固定约束')
p('使用 double、BFS、距离容差 1e-6、最大迭代数 1e6、minimum_separation=0、t_max=1。各组漏检必须为 0，误报上限按仿真 VF、仿真 EE、人工 VF、人工 EE 依次为 2/17/90/203。')
p('保留碰撞查询的 TOI 与输出容差要求与原版逐位一致。新增几何过滤必须说明保守性或误差界；测试集零漏检不能替代一般数值论证。[E3]')
sub('计时范围')
p('只比较核心计算时间，包含 API 参数转换和 CCD 调用，排除数据读取、解析、缓存转换、结果比较及写盘。历史基线 74.37439 秒仅作参考，最终加速比以同期原版为分母。')

page(); h('4. 测试集说明')
p('使用论文配套的 2020 年人工构造与仿真查询数据。人工数据用于覆盖困难和退化情形，仿真数据用于覆盖模拟中的查询；数据托管于 NYU。')
link('官方数据集：Large Scale Benchmarks for Continuous Collision Detection','https://archive.nyu.edu/handle/2451/61518')
table(['测试组','查询数量'],[['仿真点—三角形 VF','17,959,962'],['仿真边—边 EE','41,372,584'],['人工点—三角形 VF','21,208'],['人工边—边 EE','34,129'],['合计','59,387,883']],[2,1])
p('快速筛选集为 546,337 条：全部人工查询、全部仿真真碰撞，以及每个仿真文件从索引 0 开始每 128 条抽取一条，去重后固定。最终使用全部 59,387,883 条查询验证速度和正确性。[E3,E4]')
p('筛选集包含在全量集中，目前没有另设完全独立、未参与方案选择的测试集。评价指标包括核心耗时、加速比、分组漏检与误报，以及逐查询输出一致性。所用数据没有精确 TOI 真值，因此尚未独立测量绝对碰撞时间误差。')
p('表中规模来自实际发布归档的统计；人工组数量与论文表格不同，不能称为逐项复现论文所有数字。','small')
h('5. 自动流程说明')
p('① 复现并固定 baseline：核对代码、数据、参数和运行环境，保留原版工作树作为对照。\n② 建立评测入口：固定筛选集、计时范围和正确性门槛，分别构建原版与候选程序。\n③ 分析瓶颈：围绕重复计算、内存分配、搜索开销和几何过滤提出优化假设。\n④ 实现并验证：AI 修改 C++ 代码，运行定向检查与子集实验；数值判定改动补充保守性论证。\n⑤ 保留或回退：记录版本、参数、日志和失败原因，对有潜力的方案进一步做全量测试。\n⑥ 同期复测：原版与最佳候选交替运行，各至少三次，比较每轮四组时间之和的中位数。\n⑦ 按停止条件交付：保存最佳代码、验证结果与复现记录，不把构建失败和重复计时计为新候选。')
p('已完成 C01–C20 共 20 个有效候选，最终选择 C20。初期 C02 已达到 20% 目标；最终版本未达到提高后的 80% 目标。[E2]')

page(); h('6. 当前提升')
p('最新全量对照实验于 2026 年 10 月 10 日完成。两版使用同一台 Intel Core Ultra 7 265KF、Windows 11、MSVC 19.44 Release；单线程绑定逻辑 CPU 0，保持相同数据、参数和计时方式。')
table(['指标','原版','C20','改进'],[
 ['全量核心耗时中位数','72.746 秒','32.992 秒','降低 54.65%'],
 ['加速比','1×','2.205×','约 2.2 倍速度'],
 ['总漏检数','0','0','保持零漏检'],
 ['总误报数','312','191','减少 121 个'],
],[1.9,1.2,1.2,1.5])
p('误报数量下降 38.78%；该数值不是全体查询错误率的下降比例。耗时降幅仅针对核心计算，不代表整个程序端到端时间降低同样比例。')
sub('三轮同期交替运行的原始时间')
table(['轮次','原版 / 秒','C20 / 秒'],[[str(i+1),f"{s['runs']['reference'][i]['ccd_seconds']:.6f}",f"{s['runs']['candidate'][i]['ccd_seconds']:.6f}"] for i in range(3)]+[['中位数',f'{ref:.6f}',f'{best:.6f}']],[1,1.7,1.7])
sub('分组正确性')
table(['测试组','原版误报','C20 误报','C20 漏检'],[['仿真 VF',2,2,0],['仿真 EE',17,6,0],['人工 VF',90,53,0],['人工 EE',203,130,0]],[1.8,1,1,1])
p('三次 C20 的误报和漏检计数完全一致。每轮允许剔除的原版误报恰好为 121 条，其余 59,387,762 条查询的 hit、TOI、output_tolerance 共 24 字节输出与原版逐位一致。[E1]')
p('初始 20% 目标已达到；80% 目标未达到。C20 保留了原版碰撞时间输出行为，但这不等于独立验证了绝对 TOI 精度。距离容差 1e-6 不能解释成绝对时间误差上限。')
p('最终核心源码提交：0c1f229b4e10a3ad95033956f6604f5740c64c8d。[E2]','small')

page(); h('7. 创新点总结')
sub('让容易排除的查询尽早结束')
p('将原有初始盒判定前移，并加入运动包围盒过滤。对已经能证明无碰撞的查询，省去后续容差准备、队列初始化和搜索；过滤顺序也按 VF、EE 的实际成本进行调整。')
sub('把较贵的几何证书留给困难查询')
p('引入 Bernstein 共面性证书和投影分离证书：前者通过整个时间段内不共面排除碰撞，后者通过投影区间严格分离排除碰撞。证书不能确定时继续原搜索。')
p('这些证书在 BFS 搜索计数达到 refine==32 时才尝试，避免对大量简单查询统一增加较高成本。该计数不等同于每条查询都先完成了 32 次几何二分。')
sub('减少求解过程中的重复工作')
p('复用时间与空间插值结果，减少重复算术和临时分配；压紧搜索节点并复用队列容量。对误差界公式使用保守的向上舍入乘法，降低通用求值开销，同时保留数值上界依据。')
sub('当前成果的定位')
p('这些改进形成了“实现优化与保守几何过滤相结合”的版本，保留原有 BFS 区间求根框架。目前已验证组合效果，尚未通过完整消融量化各项贡献，也尚未完成足以确认学术新颖性的相关工作比较。因此，以上是本项目的具体改进点，不宜直接宣称为全新的 CCD 算法。[E5]')
sub('本地证据索引')
p('下列路径均相对于 Tight-Inclusion-autoresearch 工作树；外部论文、仓库和数据集链接见第 2、4 节。','small')
sources=[
 ('E1','最终全量结果','research-results/final80-c20-summary.json'),
 ('E2','候选审计与复现命令','research-results/final80-completion-audit.json\nresearch/FINAL_RESULTS80.rst'),
 ('E3','评测协议','research/PROTOCOL.rst'),
 ('E4','数据来源与完整性','research-results/cache/source-provenance.json'),
 ('E5','改动分析与数值依据','research/C20_CHANGE_ANALYSIS.rst\nresearch/NUMERICS.rst\nresearch/CONTINUED_NUMERICS.rst'),
]
for k,label,path in sources: p(f'[{k}] {label}\n{path}','small')

def footer(c,doc):
    c.setFont('CN',8); c.setFillColor(GRAY)
    c.drawString(50,30,'Tight-Inclusion CCD  |  研究总结  |  2026-10-16')
    c.drawRightString(W-50,30,str(doc.page))
OUT.parent.mkdir(parents=True,exist_ok=True)
SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=40,bottomMargin=47,title='Tight-Inclusion CCD 自动优化研究总结',author='').build(story,onFirstPage=footer,onLaterPages=footer)
SRC.write_text('\n'.join(rst),encoding='utf-8')
reader=PdfReader(OUT); text='\n'.join(p.extract_text() for p in reader.pages)
assert len(reader.pages)==5,len(reader.pages)
for v in ['1. 问题描述','2. Baseline','3. 目标','4. 测试集','5. 自动流程','6. 当前提升','7. 创新点','54.65%','59,387,883']: assert v in text,v
links=[a.get_object().get('/A',{}).get('/URI') for p in reader.pages for a in p.get('/Annots',[])]
assert len([x for x in links if x])==5,links
qa=dict(date='2026-10-16',pages=5,external_links=links,equations=eqnum,raw_results_checked=True,new_experiments_run=False,all_pages_visually_reviewed=False,pdf_sha256=hashlib.sha256(OUT.read_bytes()).hexdigest())
(ROOT/'research-results/study-summary-20261016-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(qa,ensure_ascii=False))
