"""Validate supplied fixtures; optionally collect repeatable host/board timings."""
from pathlib import Path
import argparse,subprocess,json,statistics,hashlib,platform,os,time
P=Path(__file__).resolve().parent
a=argparse.ArgumentParser();a.add_argument('--binary',default=str(P/'fullbench'));a.add_argument('--repeats',type=int,default=0);a.add_argument('--core',type=int);a.add_argument('--out',default=str(P.parent/'results-local'));args=a.parse_args()
out=Path(args.out);out.mkdir(exist_ok=True)
if args.repeats<0:raise SystemExit('Repetitions must be nonnegative.')
files=sorted(P.glob('frame_*_nu*.bin'))
for folder in ['band_matrix','large']:files+=sorted((P.parent/folder).glob('frame_*_nu*.bin'))
if not files:raise SystemExit('No reference fixtures found.')
summary=[]
for fixture in files:
    cmd=[args.binary,str(fixture),str(args.repeats)]
    if args.core is not None:cmd=['taskset','-c',str(args.core)]+cmd
    r=subprocess.run(cmd,capture_output=True,text=True)
    (out/(fixture.stem+'.jsonl')).write_text(r.stdout)
    if r.returncode:raise SystemExit(f'{fixture.name}: failed ({r.returncode})\n{r.stderr}')
    rows=[json.loads(l) for l in r.stdout.splitlines()];valid=[x for x in rows if x['kind']=='validation']
    if not valid or any(x['mismatch'] for x in valid):raise SystemExit('Validation failed')
    timed=[x for x in rows if x['kind']=='timing'];vs=sorted(set(x['variant'] for x in timed))
    summary.append({'file':str(fixture),'sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'validation':valid,'medians_ns':{v:statistics.median(x['ns_sample'] for x in timed if x['variant']==v) for v in vs}})
    print(fixture.name,'PASS',flush=True)
(out/'summary.json').write_text(json.dumps(summary,indent=2))
(out/'environment.json').write_text(json.dumps({'machine':platform.uname()._asdict(),'argv':vars(args),'utc_epoch':time.time(),'affinity':sorted(os.sched_getaffinity(0))},indent=2))
