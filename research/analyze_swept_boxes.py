"""Read-only diagnostic, not a CCD candidate or benchmark.

Count queries whose exact double endpoint swept AABBs are disjoint. For
linear trajectories every coordinate stays between its endpoints; separating
those closed boxes proves no exact collision for the supplied double inputs.
Report any disagreement with archive ground truth (which can originate in
rational coordinates) before considering a production filter.
"""
import json
from pathlib import Path
import numpy as np

root=Path(__file__).resolve().parents[1]
out=root/'research-results'
manifest=json.loads((out/'cache/subset-manifest.json').read_text())
answers=np.fromfile(out/'runs/ref-subset/answers-1.bin',dtype=[('toi','<f8'),('tol','<f8'),('hit','<u8')])
offset=0;results=[]
for g in range(4):
    counts=dict(group=g,queries=0,separated=0,ground_truth_positives_rejected=0,
                original_false_positives_rejected=0,original_positives_rejected=0)
    for entry in manifest:
        if entry['group']!=g:continue
        rows=np.fromfile(out/'cache/subset'/entry['path'],dtype=[('v','<f8',(8,3)),('truth','<u8')])
        v=rows['v'];n=len(rows);ref=answers[offset:offset+n];offset+=n
        ia=[0,1,4,5] if g%2 else [0,4]
        ib=[2,3,6,7] if g%2 else [1,2,3,5,6,7]
        lo_a=v[:,ia,:].min(axis=1);hi_a=v[:,ia,:].max(axis=1)
        lo_b=v[:,ib,:].min(axis=1);hi_b=v[:,ib,:].max(axis=1)
        sep=np.any((hi_a<lo_b)|(hi_b<lo_a),axis=1)
        truth=rows['truth']!=0;hit=ref['hit']!=0
        counts['queries']+=n;counts['separated']+=int(sep.sum())
        counts['ground_truth_positives_rejected']+=int((sep&truth).sum())
        counts['original_false_positives_rejected']+=int((sep&hit&~truth).sum())
        counts['original_positives_rejected']+=int((sep&hit).sum())
    results.append(counts)
assert offset==len(answers)
dest=out/'swept-box-diagnostic.json'
if dest.exists():raise FileExistsError(dest)
dest.write_text(json.dumps(dict(candidate_experiment=False,timing_claim=False,groups=results),indent=2))
print(json.dumps(results,indent=2))
