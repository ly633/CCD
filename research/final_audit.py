"""Audit the finished 20-candidate study after all timed processes have stopped."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess as sp
import zipfile
import research as r

prefix='final80-c20'
summary=json.loads((r.OUT/f'{prefix}-summary.json').read_text())
assert summary['all_correct'] and summary['queries_per_run']==59387883
assert summary['target_reduction']==.8
ledger=[]
for n in range(1,21):
    name=f'C{n:02d}'
    meta=json.loads((r.OUT/f'c{n:02d}-experiment.json').read_text())
    completed=[]
    for path in sorted((r.OUT/'runs').glob(f'c{n:02d}-subset*/results.json')):
        run=json.loads(path.read_text())
        if run.get('valid') and run.get('runs'):
            assert run['dataset']=='subset' and run['kind']=='candidate'
            for item in run['runs']:
                assert sum(g['queries'] for g in item['groups'])==546337
                assert all(g['fn']==0 for g in item['groups'])
            completed.append(str(path.relative_to(r.ROOT)))
    assert completed,(name,'no actual valid fixed-subset experiment')
    sp.run(['git','cat-file','-e',meta['revision']+'^{commit}'],cwd=r.ROOT,check=True)
    ledger.append(dict(id=name,revision=meta['revision'],valid=True,effective_experiment=True,
        hypothesis=meta['hypothesis'],subset_seconds=meta.get('subset_seconds',meta.get('subset_candidate_seconds')),
        completed_subset_reports=completed,status=meta['status']))

assert r.git('-C',str(r.ROOT.parent/'Tight-Inclusion'),'status','--porcelain')==''
assert (r.ROOT/'scripts/run-baseline.py').read_text(encoding='utf-8')==(r.ROOT.parent/'Tight-Inclusion/scripts/run-baseline.py').read_text(encoding='utf-8')
assert r.git('diff','5b7763c','--','scripts/run-baseline.py')==''
reference_files=r.git('ls-tree','-r','--name-only','v1.0.6','src').splitlines()
for name in reference_files:
    assert (r.ROOT/'research/reference'/name).read_bytes()==sp.check_output(['git','show','v1.0.6:'+name],cwd=r.ROOT)

cache=r.OUT/'cache'
ready=json.loads((cache/'ready.json').read_text())
cache_files=cache_bytes=0
for kind in ('full','subset'):
    manifest=cache/f'{kind}-manifest.json'
    assert r.sha(manifest)==ready['inventories'][kind]['manifest_sha256']
    entries=json.loads(manifest.read_text())
    assert sum(x['queries'] for x in entries)==ready['inventories'][kind]['queries']
    for entry in entries:
        path=cache/kind/entry['path']
        assert path.stat().st_size==entry['queries']*200
        assert r.sha(path)==entry['sha256'],str(path)
        cache_files+=1;cache_bytes+=path.stat().st_size
assert r.sha(cache/'source-manifest.json')==ready['source_manifest_sha256']

binary_hashes={}
for kind in ('reference','candidate'):
    digests=set()
    for i in range(1,4):
        path=r.OUT/'runs'/f'{prefix}-{kind}-{i}'
        report=json.loads((path/'results.json').read_text())
        exe=path/f'research_{kind}.exe'
        assert r.sha(exe)==report['executable_sha256']
        assert 'FP_ENV MXCSR=8064 ROUND=FE_TONEAREST FTZ=0 DAZ=0' in (path/'run-1.log').read_text()
        for name,digest in report['core_source'].items():
            assert r.sha(path/'src'/name)==digest
        digests.add(r.sha(exe))
    assert len(digests)==1
    binary_hashes[kind]=digests.pop()

best=r.OUT/'runs/c20-subset'
best_report=json.loads((best/'results.json').read_text())
assert best_report['executable_sha256']==binary_hashes['candidate']
for name,digest in best_report['core_source'].items():
    assert r.sha(r.ROOT/'src'/name)==digest,('working source differs from measured best',name)
best_revision='0c1f229b4e10a3ad95033956f6604f5740c64c8d'
patch=sp.check_output(['git','diff','v1.0.6',best_revision,'--','src'],cwd=r.ROOT)
(r.OUT/'best-c20-core.patch').write_bytes(patch)
with zipfile.ZipFile(r.OUT/'best-c20-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((best/'src').rglob('*')):
        if path.is_file():archive.write(path,Path('src')/path.relative_to(best/'src'))
with zipfile.ZipFile(r.OUT/'best-c20-source.zip') as archive:
    for name,digest in best_report['core_source'].items():
        assert hashlib.sha256(archive.read('src/'+name.replace('\\','/'))).hexdigest()==digest

audit=dict(checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    effective_candidates=20,candidate_ledger=ledger,performance_target_met=summary['target_passed'],
    stopping_condition='20 effective candidate experiments completed; final full comparison and delivery verified',
    all_full_runs_correct=True,reference_source_files_verified=len(reference_files),
    baseline_worktree_clean=True,baseline_guard_unchanged=True,
    guard_comparison='Identical normalized text to baseline; no Git change since research setup. Checkout line endings differ.',
    cache_files_rehashed=cache_files,cache_bytes_rehashed=cache_bytes,
    executable_sha256=binary_hashes,best_source_revision=best_revision,
    working_source_matches_tested_best=True,core_zip_sha256=r.sha(r.OUT/'best-c20-source.zip'),
    rigorous_error_bound_checks=json.loads((r.OUT/'error-bound-audit/result.json').read_text())['checks'],
    final_summary=f'{prefix}-summary.json')
r.save(r.OUT/'final80-completion-audit.json',audit)
print(json.dumps({k:v for k,v in audit.items() if k!='candidate_ledger'},indent=2))
