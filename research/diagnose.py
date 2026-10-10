"""Collect slow-query diagnostics; never use these timings as a candidate result."""
import argparse
import json
import subprocess as sp
import shutil
import research as r

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--id',required=True)
a=p.parse_args()
out=r.OUT/'diagnostics'/a.id
out.mkdir(parents=True,exist_ok=False)
with (out/'build.log').open('wb') as log:
    sp.run(['cmake','--build',str(r.BUILD),'--config','Release','--target','research_diagnostic','--parallel','8'],cwd=r.ROOT,stdout=log,stderr=sp.STDOUT,check=True)
exe=r.BUILD/'research/Release/research_diagnostic.exe'
shutil.copy2(exe,out/exe.name)
shutil.copy2(exe.parent/'gmp.dll',out/'gmp.dll')
r.pin()
cmd=[str(out/exe.name),'run',str(r.OUT/'cache/subset.txt'),str(r.OUT/'cache/subset'),str(out/'answers.bin')]
with (out/'run.log').open('wb') as log:
    sp.run(cmd,cwd=r.ROOT,stdout=log,stderr=sp.STDOUT,check=True)
slow=[]
for line in (out/'run.log').read_text().splitlines():
    if line.startswith('SLOW '):
        _,g,path,index,truth,hit,toi,seconds=line.split()
        slow.append(dict(group=int(g),path=path,index=int(index),truth=int(truth),hit=int(hit),toi=toi,seconds=float(seconds)))
slow.sort(key=lambda x:-x['seconds'])
report=dict(revision=r.git('rev-parse','HEAD'),executable_sha256=r.sha(exe),diagnostic_only=True,slow_queries=len(slow),
            slow_seconds=sum(x['seconds'] for x in slow),slow_true_seconds=sum(x['seconds'] for x in slow if x['truth']),
            slow_false_seconds=sum(x['seconds'] for x in slow if not x['truth']),queries=slow)
r.save(out/'summary.json',report)
print(json.dumps({k:v for k,v in report.items() if k!='queries'},indent=2))
print(json.dumps(slow[:12],indent=2))
