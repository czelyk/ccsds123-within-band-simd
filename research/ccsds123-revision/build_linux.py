"""Build native or cross-compiled RVV Linux pilot; execution is separate."""
from pathlib import Path
import argparse,subprocess,json,hashlib,os
R=Path(__file__).resolve().parent;S=R/'src';K=S/'reference_kernels'
p=argparse.ArgumentParser();p.add_argument('--sysroot');p.add_argument('--gcc-dir');p.add_argument('--lld');a=p.parse_args()
cmd=[os.environ.get('CC','clang-18'),'-O3','-march=rv64gcv_zba_zbb','-mabi=lp64d','-DRVV_NATIVE','-I',str(K),'-I',str(S)]
if a.sysroot:
 if not a.gcc_dir or not a.lld:raise SystemExit('Cross-build requires sysroot, gcc-dir and lld')
 cmd+=['--target=riscv64-linux-gnu','--sysroot='+str(Path(a.sysroot).resolve()),'--gcc-install-dir='+str(Path(a.gcc_dir).resolve()),'--ld-path='+str(Path(a.lld).resolve()),'-static']
sources=[S/'native_bench.c']+[K/f'{kind}{c}.c' for kind in ('scalar','rvv','frozen_rvv') for c in range(3,7)]
cmd+=list(map(str,sources))+['-o',str(R/'build/revision-pilot-rvv')]
result=subprocess.run(cmd,capture_output=True,text=True);(R/'build/linux-build.log').write_text(result.stdout+result.stderr)
manifest={'command':cmd,'returncode':result.returncode,'execution':'not run on physical hardware','sources':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}}
if result.returncode==0:manifest['elf_sha256']=hashlib.sha256((R/'build/revision-pilot-rvv').read_bytes()).hexdigest()
(R/'build/linux-build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(result.stdout+result.stderr);raise SystemExit(result.returncode)
