"""Functional RVV checks; model execution time is not physical performance."""
from pathlib import Path
import subprocess,struct,json,hashlib,os,time,shutil
R=Path(__file__).resolve().parent;project=R.parent.parent
renode=os.environ.get('RENODE') or shutil.which('renode')
if not renode:raise SystemExit('Set RENODE to the executable, or install Renode on PATH.')
elf=R/'build/revision-selftest.elf';platform=R/'src/reference_kernels/rvv.repl'
records=[]
for vl in (128,256,512,1024):
    status=R/f'evidence/rvv-status-{vl}.bin';script=R/f'build/rvv-check-{vl}.resc'
    status.unlink(missing_ok=True)
    script.write_text(f'mach create\nmachine LoadPlatformDescription @{platform}\ncpu VectorRegisterLength {vl}\ncpu PerformanceInMips 100\nsysbus LoadELF @{elf}\nemulation RunFor "24"\ndump_file 0x80000000 64 "{status}"\nquit\n')
    start=time.monotonic()
    p=subprocess.run([renode,'--plain','--disable-gui','-P','-1',str(script)],capture_output=True,text=True,timeout=120)
    (R/f'evidence/rvv-check-{vl}.log').write_text(p.stdout+p.stderr)
    row={'VLEN':vl,'returncode':p.returncode,'wall_seconds':time.monotonic()-start,'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),'scope':'new conventional baselines vs scalar, body/residual/final-state differential validation; not physical performance or independent conformance'}
    if status.exists():row['status']=list(struct.unpack('<8Q',status.read_bytes()))
    row['pass']=p.returncode==0 and row.get('status',[0])[0]==0x600dcc53 and row['status'][1]==2016 and row['status'][2]==0 and row['status'][3]==4249224 and row['status'][4]==144
    records.append(row)
    (R/'evidence/rvv-validation.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(row),flush=True)
assert all(r['pass'] for r in records),'A functional check failed or did not finish; preserve logs and investigate.'
