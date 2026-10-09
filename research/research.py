"""Audited, single-thread CCD research. Run from any directory; no baseline writes."""
import argparse
import concurrent.futures as cf
import ctypes
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess as sp
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research-results'
DATA = ROOT.parent / 'Tight-Inclusion/external/baseline/Full-CCD-2020'
BUILD = ROOT / 'build-autoresearch-sample'
GROUPS = ['simulation/vertex-face','simulation/edge-edge','handcrafted/vertex-face','handcrafted/edge-edge']
PARAMS = dict(precision='double', tolerance=1e-6, max_iterations=1000000,
              minimum_separation=0, t_max=1, no_zero_toi=False,
              numerical_error=[-1,-1,-1], method='BREADTH_FIRST_SEARCH')

def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def save(p, data):
    Path(p).write_text(json.dumps(data,indent=2),encoding='utf-8')

def git(*args):
    return sp.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()

def pin():
    os.environ.update(OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    if not k.SetProcessAffinityMask(k.GetCurrentProcess(),1): raise ctypes.WinError(ctypes.get_last_error())

def init():
    ref=ROOT/'research/reference'
    ref.mkdir(parents=True,exist_ok=True)
    for f in git('ls-tree','-r','--name-only','v1.0.6','src').splitlines():
        p=ref/f
        if p.exists():
            if p.read_bytes()!=sp.check_output(['git','show',f'v1.0.6:{f}'],cwd=ROOT): raise RuntimeError(f'changed reference {f}')
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(sp.check_output(['git','show',f'v1.0.6:{f}'],cwd=ROOT))
    OUT.mkdir(exist_ok=True)
    save(OUT/'environment.json',dict(time=dt.datetime.now().astimezone().isoformat(),
        platform=platform.platform(),python=platform.python_version(),
        upstream=git('rev-parse','v1.0.6'),start_revision=git('rev-parse','HEAD'),
        baseline_status=git('-C',str(ROOT.parent/'Tight-Inclusion'),'status','--porcelain'),
        baseline_core_diff=git('-C',str(ROOT.parent/'Tight-Inclusion'),'diff','v1.0.6','--','src','app','CMakeLists.txt','cmake'),
        parameters=PARAMS,cpu=0,threads=1))

def prepare(workers):
    out=OUT/'cache'
    out.mkdir(exist_ok=True)
    manifest=json.loads((DATA/'dataset-manifest.json').read_text())
    entries=[(g,f) for g,key in enumerate(GROUPS) for f in sorted(manifest[key]['files'],key=lambda x:x['path'])]
    assert sum(f['queries'] for _,f in entries)==59387883
    if (out/'ready.json').exists(): raise FileExistsError('cache already prepared')
    shutil.copy2(DATA/'dataset-manifest.json',out/'source-manifest.json')
    shutil.copy2(DATA/'provenance.json',out/'source-provenance.json')
    def worker(w):
        chunk=entries[w::workers]
        path=out/f'pack-{w}.txt'
        path.write_text(''.join(f"{g} {f['queries']} {f['path']}\n" for g,f in chunk))
        for _,f in chunk:
            p=DATA/f['path']
            if p.stat().st_size!=f['bytes'] or sha(p)!=f['sha256']: raise RuntimeError(f'CSV integrity {p}')
        print(f'worker {w}: source SHA256 verified; packing {len(chunk)} files',flush=True)
        with (out/f'pack-{w}.log').open('wb') as log:
            sp.run([str(BUILD/'research/Release/research_reference.exe'),'pack',str(path),str(DATA),str(out)],cwd=ROOT,stdout=log,stderr=sp.STDOUT,check=True)
        print(f'worker {w}: packed',flush=True)
    with cf.ThreadPoolExecutor(workers) as pool: list(pool.map(worker,range(workers)))
    inventories={}
    for kind in ('full','subset'):
        inv=[]
        for g,f in entries:
            rel=f['path']+'.bin'; p=out/kind/rel
            assert p.stat().st_size%200==0
            count=p.stat().st_size//200
            if kind=='full': assert count==f['queries']
            inv.append(dict(group=g,path=rel,queries=count,sha256=sha(p)))
        (out/f'{kind}.txt').write_text(''.join(f"{f['group']} {f['queries']} {f['path']}\n" for f in inv))
        save(out/f'{kind}-manifest.json',inv)
        inventories[kind]=dict(queries=sum(f['queries'] for f in inv),manifest_sha256=sha(out/f'{kind}-manifest.json'))
    save(out/'ready.json',dict(inventories=inventories,source_manifest_sha256=sha(DATA/'dataset-manifest.json'),
         conversion='Unchanged pinned CCD-Query-IO GMP reader; native little-endian 24 doubles + uint64 truth; every CSV SHA256 revalidated',
         subset='All handcrafted + every 128th simulation query per CSV (index 0,128,...) + all simulation ground-truth positives; sorted relative CSV paths',
         preparation_workers=workers,preparation_excluded_from_timing=True))
    print(json.dumps(inventories),flush=True)

def run(args):
    pin()
    out=OUT/'runs'/args.id
    out.mkdir(parents=True,exist_ok=False)
    cache=OUT/'cache'
    ready=json.loads((cache/'ready.json').read_text())
    exe=BUILD/f'research/Release/research_{args.kind}.exe'
    shutil.copy2(exe,out/exe.name); shutil.copy2(exe.parent/'gmp.dll',out/'gmp.dll')
    source = ROOT/'src' if args.kind=='candidate' else ROOT/'research/reference/src'
    shutil.copytree(source,out/'src')
    shutil.copy2(ROOT/'research/runner.cpp',out/'runner.cpp')
    shutil.copy2(BUILD/'CMakeCache.txt',out/'CMakeCache.txt')
    (out/'source.patch').write_text(git('diff','v1.0.6','--','src','app','CMakeLists.txt','research'),encoding='utf-8')
    expected=Path(args.expected).resolve() if args.expected else None
    reference=json.loads((expected/'results.json').read_text()) if expected else None
    report=dict(id=args.id,kind=args.kind,dataset=args.dataset,hypothesis=args.hypothesis,
        created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),revision=git('rev-parse','HEAD'),
        core_source={str(p.relative_to(source)):sha(p) for p in sorted(source.rglob('*')) if p.is_file()},
        build_settings=[l for l in (BUILD/'CMakeCache.txt').read_text().splitlines() if l.startswith(('CMAKE_CXX_FLAGS','TIGHT_INCLUSION_','CMAKE_GENERATOR','Eigen3_DIR','GMP_'))],
        executable_sha256=sha(exe),runner_sha256=sha(ROOT/'research/runner.cpp'),
        parameters=PARAMS,logical_cpu=0,threads=1,cache=ready,
        timing='Unchanged upstream per-query Timer; includes API argument conversion and CCD call; excludes cache/CSV I/O, result comparison, hashing and writes',
        expected=str(expected) if expected else None,runs=[])
    save(out/'results.json',report)
    for i in range(1,args.repeats+1):
        cmd=[str(out/exe.name),'run',str(cache/f'{args.dataset}.txt'),str(cache/args.dataset),str(out/f'answers-{i}.bin')]
        if expected: cmd.append(str(expected/'answers-1.bin'))
        print(f'{args.id} run {i} starting',flush=True)
        t=time.perf_counter()
        with (out/f'run-{i}.log').open('wb') as log:
            proc=sp.run(cmd,cwd=ROOT,stdout=log,stderr=sp.STDOUT)
        item=dict(command=cmd,exit_code=proc.returncode,wall_seconds=time.perf_counter()-t,groups=[])
        report['runs'].append(item)
        for line in (out/f'run-{i}.log').read_text(encoding='utf-8',errors='replace').splitlines():
            if line.startswith('RESULT '):
                _,g,n,gt,fp,fn,sec,mm,h=line.split()
                item['groups'].append(dict(group=GROUPS[int(g)],queries=int(n),positives=int(gt),fp=int(fp),fn=int(fn),ccd_seconds=float(sec),bitwise_mismatches=int(mm),output_hash=h))
        item['ccd_seconds']=sum(g['ccd_seconds'] for g in item['groups'])
        valid=proc.returncode==0 and len(item['groups'])==4
        if valid:
            valid &= sum(g['queries'] for g in item['groups'])==ready['inventories'][args.dataset]['queries']
            for g,cap in zip(item['groups'],[2,17,90,203]):
                valid &= g['fn']==0 and g['fp']<=cap and g['bitwise_mismatches']==0
            if reference:
                valid &= args.dataset==reference['dataset']
                valid &= all(g['fp']<=ref['fp'] for g,ref in zip(item['groups'],reference['runs'][0]['groups']))
        item['valid']=bool(valid)
        save(out/'results.json',report)
        print(f"{args.id} run {i}: CCD={item['ccd_seconds']:.9f}s valid={valid}",flush=True)
        if not valid: raise RuntimeError(f'validation failed: {out}')
    report['median_ccd_seconds']=statistics.median(r['ccd_seconds'] for r in report['runs'])
    report['valid']=all(r['valid'] for r in report['runs'])
    save(out/'results.json',report)

def main():
    p=argparse.ArgumentParser(description=__doc__); subs=p.add_subparsers(dest='cmd',required=True)
    subs.add_parser('init')
    prep=subs.add_parser('prepare');prep.add_argument('--workers',type=int,default=8)
    r=subs.add_parser('run');r.add_argument('--id',required=True)
    r.add_argument('--kind',choices=['reference','profile','candidate'],required=True)
    r.add_argument('--dataset',choices=['subset','full'],default='subset')
    r.add_argument('--repeats',type=int,default=1);r.add_argument('--expected')
    r.add_argument('--hypothesis',required=True)
    args=p.parse_args()
    if args.cmd=='init': init()
    elif args.cmd=='prepare': prepare(args.workers)
    else: run(args)
if __name__=='__main__': main()
