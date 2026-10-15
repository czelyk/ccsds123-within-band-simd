from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parent;ORIG=ROOT/'src/reference_kernels'
s=(ROOT/'src/tap_host.c').read_text()
s=s.replace('static size_t run(Frame*f,int variant,Counts*counts){','#include "native_bip.inc"\nstatic size_t run(Frame*f,int variant,Counts*counts){\nif(variant==9)return native_bip(f);')
s=s.replace('(learn_lines||variant==0)?weights:0','(learn_lines||variant==0||variant==9)?weights:0')
(ROOT/'src/native_bip_host.c').write_text(s)
sources=[ROOT/'src/native_bip_host.c']+[ORIG/f'{typ}{c}.c' for typ in ('scalar','avx','frozen') for c in range(3,7)]
cmd=['clang-18','-O3','-march=native','-shared','-fPIC','-I',str(ORIG),'-I',str(ROOT/'src'),*map(str,sources),'-o',str(ROOT/'build/libnativebip.so')]
r=subprocess.run(cmd,capture_output=True,text=True)
(ROOT/'build/native-bip-build.log').write_text(r.stdout+r.stderr)
(ROOT/'build/native-bip-manifest.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'src/native_bip.inc']}},indent=2)+'\n')
print(json.dumps({'returncode':r.returncode,'source_sha256':hashlib.sha256(s.encode()).hexdigest()}))
if r.returncode:raise SystemExit(r.returncode)
# Separate validation-only build: capture every mapped residual in common
# (band, spatial-index) order. Do not time this instrumented build.
capture=s.replace('static inline void encode(Writer*w,Entropy*e,unsigned delta,size_t t){','static Entropy *capture_states; static uint32_t *capture_output; static size_t capture_n;\nstatic inline void encode(Writer*w,Entropy*e,unsigned delta,size_t t){\nif(capture_output)capture_output[(size_t)(e-capture_states)*capture_n+t]=delta;')
capture=capture.replace('int32_t weights[128][6];Entropy states[128];','int32_t weights[128][6];Entropy states[128];capture_states=states;capture_n=f->n;')
native=(ROOT/'src/native_bip.inc').read_text().replace('int32_t wi[6][136]={{0}};','int32_t wi[6][136]={{0}};capture_states=states;capture_n=f->n;')
capture=capture.replace('#include "native_bip.inc"',native)
capture+='\nuint64_t capture_compute(void*v,int variant,int group,int32_t*weights,uint8_t*out,uint64_t*counts,uint32_t*residuals){capture_output=residuals;uint64_t n=compute(v,variant,group,0,weights,out,counts,0);capture_output=0;return n;}\n'
(ROOT/'src/native_bip_capture.c').write_text(capture)
capturecmd=[str(ROOT/'src/native_bip_capture.c') if v==str(sources[0]) else str(ROOT/'build/libcapture.so') if v==str(ROOT/'build/libnativebip.so') else v for v in cmd]
rc=subprocess.run(capturecmd,capture_output=True,text=True)
(ROOT/'build/capture-build.log').write_text(rc.stdout+rc.stderr)
(ROOT/'build/capture-manifest.json').write_text(json.dumps({'command':capturecmd,'returncode':rc.returncode,'source_sha256':hashlib.sha256(capture.encode()).hexdigest()},indent=2)+'\n')
print(json.dumps({'capture_returncode':rc.returncode}));raise SystemExit(rc.returncode)
