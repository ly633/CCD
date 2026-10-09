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
p.add_argument('--allow-fp-removal',action='store_true')
p.add_argument('--resume',action='store_true',help='Retry unchanged binaries after an execution failure; never rebuild or replace them')
a=p.parse_args()
identifier=a.id.lower()
record_path=r.OUT/f'{identifier}-experiment.json'
if record_path.exists() and not a.resume:raise FileExistsError(record_path)
record=json.loads(record_path.read_text()) if a.resume else dict(id=a.id,parent=a.parent,hypothesis=a.hypothesis,revision=r.git('rev-parse','HEAD'),
            numerical_argument='research/CONTINUED_NUMERICS.rst',status='building',
            build_log=f'{identifier}-build.log',focused_test=f'{identifier}-equivalence.log')
r.save(record_path,record)
if not a.resume:
    with (r.OUT/record['build_log']).open('wb') as log:
        proc=sp.run(['cmake','--build',str(r.BUILD),'--config','Release','--target','research_reference','research_candidate','research_equivalence','--parallel','8'],cwd=r.ROOT,stdout=log,stderr=sp.STDOUT)
    record['build_exit_code']=proc.returncode
    if proc.returncode:
        record.update(status='build failed',effective_experiment=False);r.save(record_path,record);sys.exit(1)
    record['built_hashes']={name:r.sha(r.BUILD/f'research/Release/{name}.exe') for name in ('research_candidate','research_equivalence')}
else:
    for name,digest in record['built_hashes'].items():
        if r.sha(r.BUILD/f'research/Release/{name}.exe')!=digest:raise RuntimeError('Resume requires the exact unchanged executable')
attempt=len(record.get('focused_attempts',[]))+1
focused_log=record['focused_test'] if attempt==1 else f'{identifier}-equivalence-attempt-{attempt}.log'
record.setdefault('focused_attempts',[]).append(dict(log=focused_log))
r.save(record_path,record)
try:
    with (r.OUT/focused_log).open('wb') as log:
        test=sp.run([str(r.BUILD/'research/Release/research_equivalence.exe')],cwd=r.ROOT,stdout=log,stderr=sp.STDOUT)
except OSError as error:
    record['focused_attempts'][-1].update(winerror=getattr(error,'winerror',None),message=str(error),started=False)
    record.update(status='focused test process creation blocked',effective_experiment=False,valid=False)
    r.save(record_path,record);print('Execution blocked; original binary retained:',error,flush=True);sys.exit(1)
record['focused_attempts'][-1].update(exit_code=test.returncode,started=True)
record['focused_exit_code']=test.returncode
# A failed targeted test is still followed by the fixed dataset to quantify the
# failure. No failed candidate can be selected merely because aggregate FP/FN pass.
run_id=f'{identifier}-subset'
original_run=r.OUT/'runs'/run_id
if original_run.exists():
    if not a.resume:raise FileExistsError(original_run)
    run_id=f'{identifier}-subset-retry-{attempt}'
cmd=[sys.executable,str(r.ROOT/'research/research.py'),'run','--id',run_id,
     '--kind','candidate','--expected',str(r.OUT/'runs/ref-subset'),'--hypothesis',a.hypothesis,
     '--repeats',str(a.repeats)]
if a.allow_fp_removal:cmd.append('--allow-fp-removal')
if original_run.exists():cmd.extend(['--snapshot',str(original_run)])
record['command']=cmd;r.save(record_path,record)
proc=sp.run(cmd,cwd=r.ROOT)
result=json.loads((r.OUT/'runs'/run_id/'results.json').read_text())
record['result_directory']=str(r.OUT/'runs'/run_id)
if not result['runs']:
    record.update(effective_experiment=False,valid=False,status='execution blocked before dataset evaluation',
                  execution_error=result.get('execution_error'),subset_exit_code=proc.returncode)
    r.save(record_path,record);sys.exit(proc.returncode or 1)
record.update(effective_experiment=True,subset_exit_code=proc.returncode,
    valid=proc.returncode==0 and test.returncode==0,
    subset_seconds=result.get('median_ccd_seconds',result['runs'][0]['ccd_seconds']),
    bitwise_mismatches=sum(g['bitwise_mismatches'] for run in result['runs'] for g in run['groups']),
    groups=result['runs'][0]['groups'],status='screened; selection pending')
if not record['valid']:record.update(status='rejected',failure_reason='Focused or dataset equality/correctness check failed')
r.save(record_path,record)
print(json.dumps({k:record[k] for k in ('id','valid','subset_seconds','bitwise_mismatches')},indent=2),flush=True)
