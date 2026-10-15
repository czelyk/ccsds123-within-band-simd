from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parent;S=R/'src';K=S/'reference_kernels'
old=S/'prior_native_bip_host.c'
s=old.read_text()
native=(S/'native_bip_rvv.inc').read_text();native=native[native.index('static size_t native_bip_scalar'):native.index('static size_t native_bip(Frame*f)')]
native=native.replace('if(component_lmul)p=component_update(u,sigma,2*s,weights[z],c,r,component_lmul);\n            else{','(void)component_lmul;{')
assert 'component_update' not in native
s=s.replace('static size_t run(Frame*f,int variant,Counts*counts){',native+'\nstatic size_t run(Frame*f,int variant,Counts*counts){\nif(variant==11)return native_bip_scalar(f,0);',1)
(S/'pilot_host.c').write_text(s)
sources=[S/'pilot_host.c']+[K/f'{typ}{c}.c' for typ in ('scalar','avx','frozen') for c in range(3,7)]
cmd=['clang-18','-O3','-march=native','-shared','-fPIC','-I',str(K),'-I',str(S),*map(str,sources),'-o',str(R/'build/libpilot.so')]
p=subprocess.run(cmd,capture_output=True,text=True);(R/'build/host-build.log').write_text(p.stdout+p.stderr)
(R/'build/host-build-manifest.json').write_text(json.dumps({'command':cmd,'returncode':p.returncode,'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'scope':'processed L1 resident replay, not physical RVV'},indent=2)+'\n')
print(p.stderr);raise SystemExit(p.returncode)
