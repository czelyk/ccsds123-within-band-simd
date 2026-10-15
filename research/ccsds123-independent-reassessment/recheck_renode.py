from pathlib import Path
import subprocess,hashlib,shutil,struct,json,os
R=Path(__file__).resolve().parent;project=R.parent.parent;old=R.parent/'iac2027-vector-compression-kit/src'
renode=os.environ.get('RENODE') or shutil.which('renode')
if not renode:raise SystemExit('Set RENODE to the executable, or install Renode on PATH.')
elf=R/'build/original-selftest.elf';platform=R/'build/original-rvv.repl'
if (old/'selftest.elf').exists():
    shutil.copyfile(old/'selftest.elf',elf);shutil.copyfile(old/'rvv.repl',platform)
assert elf.exists() and platform.exists(),'Packaged original ELF/platform or original kit required'
rows=[]
for length in (128,256):
    status=R/f'evidence/renode-recheck-{length}.bin';script=R/f'build/renode-recheck-{length}.resc'
    script.write_text(f'mach create\nmachine LoadPlatformDescription @{platform}\ncpu VectorRegisterLength {length}\ncpu PerformanceInMips 100\nsysbus LoadELF @{elf}\nemulation RunFor "1"\ndump_file 0x80000000 64 "{status}"\nquit\n')
    status.unlink(missing_ok=True)
    result=subprocess.run([str(renode),'--plain','--disable-gui','-P','-1',str(script)],capture_output=True,text=True,timeout=45)
    (R/f'evidence/renode-recheck-{length}.log').write_text(result.stdout+result.stderr)
    row={'VLEN':length,'returncode':result.returncode,'original_elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),'scope':'unchanged original predictor kernels, not new 120-band host baseline or physical timing'}
    if status.exists():row['status']=list(struct.unpack('<8Q',status.read_bytes()))
    row['pass']=result.returncode==0 and 'status' in row and row['status'][0]==0x600dcc53 and row['status'][1]==65914 and row['status'][2]==0
    rows.append(row);print(json.dumps(row),flush=True)
(R/'evidence/renode-reproducibility.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(r['pass'] for r in rows),'Original Renode functional reproduction failed'
