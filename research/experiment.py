"""Build and evaluate one implemented candidate, preserving even failed evidence."""
import argparse
import json
import subprocess as sp
import sys
import time
from pathlib import Path
import research as r

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--id',required=True)
p.add_argument('--parent',required=True)
p.add_argument('--hypothesis',required=True)
p.add_argument('--repeats',type=int,default=1)
a=p.parse_args()
identifier=a.id.lower()
record_path=r.OUT/f'{identifier}-experiment.json'
if record_path.exists():raise FileExistsError(record_path)
record=dict(id=a.id,parent=a.parent,hypothesis=a.hypothesis,revision=r.git('rev-parse','HEAD'),
            numerical_argument='research/CONTINUED_NUMERICS.rst',status='building',
            build_log=f'{identifier}-build.log',focused_test=f'{identifier}-equivalence.log')
r.save(record_path,record)
with (r.OUT/record['build_log']).open('wb') as log:
    proc=sp.run(['cmake','--build',str(r.BUILD),'--config','Release','--target','research_candidate','research_equivalence','--parallel','8'],cwd=r.ROOT,stdout=log,stderr=sp.STDOUT)
record['build_exit_code']=proc.returncode
if proc.returncode:
    record.update(status='build failed',effective_experiment=False);r.save(record_path,record);sys.exit(1)
with (r.OUT/record['focused_test']).open('wb') as log:
    test=sp.run([str(r.BUILD/'research/Release/research_equivalence.exe')],cwd=r.ROOT,stdout=log,stderr=sp.STDOUT)
record['focused_exit_code']=test.returncode
# A failed targeted test is still followed by the fixed dataset to quantify the
# failure. No failed candidate can be selected merely because aggregate FP/FN pass.
cmd=[sys.executable,str(r.ROOT/'research/research.py'),'run','--id',f'{identifier}-subset',
     '--kind','candidate','--expected',str(r.OUT/'runs/ref-subset'),'--hypothesis',a.hypothesis,
     '--repeats',str(a.repeats)]
record['command']=cmd;r.save(record_path,record)
proc=sp.run(cmd,cwd=r.ROOT)
result=json.loads((r.OUT/'runs'/f'{identifier}-subset'/'results.json').read_text())
record.update(effective_experiment=True,subset_exit_code=proc.returncode,
    valid=proc.returncode==0 and test.returncode==0,
    subset_seconds=result.get('median_ccd_seconds',result['runs'][0]['ccd_seconds']),
    bitwise_mismatches=sum(g['bitwise_mismatches'] for run in result['runs'] for g in run['groups']),
    groups=result['runs'][0]['groups'],status='screened; selection pending')
if not record['valid']:record.update(status='rejected',failure_reason='Focused or dataset equality/correctness check failed')
r.save(record_path,record)
print(json.dumps({k:record[k] for k in ('id','valid','subset_seconds','bitwise_mismatches')},indent=2),flush=True)
