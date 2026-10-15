"""Build functional RVV comparators without modifying the historical kit."""
from pathlib import Path
import subprocess,hashlib,json,shutil,os
R=Path(__file__).resolve().parent;S=R/'src';K=S/'reference_kernels'
s=(S/'followup_host.c').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='526aac8a93ca5b91e502e018d8252dd8bcfe0aaf854f6177f5a621dce9b58bf8'
s=s.replace('typedef struct {int width,height,bands', '#ifdef BARE\nvoid *memcpy(void*,const void*,size_t);\nvoid *memset(void*,int,size_t);\n#endif\ntypedef struct {int width,height,bands',1)
s=s.replace('static uint64_t tick(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;}', '#ifdef BARE\nstatic uint64_t tick(void){return 0;}\n#else\nstatic uint64_t tick(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;}\n#endif')
start=s.index('#ifdef VECTOR_RVV\n#include "band_rvv.inc"')
end=s.index('static size_t run(Frame*f,int variant,Counts*counts){',start)
helpers=(S/'native_bip.inc').read_text();helpers=helpers[helpers.index('static inline int bip_sample'):helpers.index('static size_t native_bip(Frame*f)')]
s=s[:start]+'#include "tap_rvv.inc"\n#include "spectral_rvv.inc"\n'+helpers+'\n#include "native_bip_rvv.inc"\n'+s[end:]
s=s.replace('static size_t run(Frame*f,int variant,Counts*counts){','static size_t run(Frame*f,int variant,Counts*counts){\nif(variant==9)return native_bip(f);\nif(variant==11)return native_bip_scalar(f,0);\nif(variant==12||variant==13)return native_bip_scalar(f,variant==12?2:1);',1)
s=s.replace('if(variant==0||variant==5){(variant==0?fused[c-3]:eager[c-3])(f,z,y,&bw,weights[z],states+z);}', 'if(variant==8||variant==10){component_row(f,z,y,&bw,weights[z],states+z,variant==8?2:1);}\nelse if(variant==0||variant==5){(variant==0?fused[c-3]:eager[c-3])(f,z,y,&bw,weights[z],states+z);}',1)
s=s.replace('\nvoid* make_context(', '\n#ifndef BARE\nvoid* make_context(',1)+'\n#endif\n'
s=s.replace('(learn_lines||variant==0)?weights:0','weights')
(S/'revision_harness.c').write_text(s)
# Validation-only instrumentation. Never use this build for performance.
capture=s.replace('static inline void encode(Writer*w,Entropy*e,unsigned delta,size_t t){','static Entropy *capture_states;static uint32_t *capture_values;static size_t capture_n;\nstatic inline void encode(Writer*w,Entropy*e,unsigned delta,size_t t){\nif(capture_values)capture_values[(size_t)(e-capture_states)*capture_n+t]=delta;')
capture=capture.replace('Writer writers[128];Entropy states[128];size_t bits[128];','Writer writers[128];Entropy states[128];size_t bits[128];capture_states=states;')
capture=capture.replace('int32_t weights[128][6];Entropy states[128];','int32_t weights[128][6];Entropy states[128];capture_states=states;')
# Includes retain their normal, uninstrumented source files separately.
native=(S/'native_bip_rvv.inc').read_text()
native=native.replace('int32_t weights[128][6];','int32_t weights[128][6];capture_states=states;')
native=native.replace('int32_t wi[6][128]={{0}};','int32_t wi[6][128]={{0}};capture_states=states;')
capture=capture.replace('#include "native_bip_rvv.inc"',native)
(S/'revision_capture.c').write_text(capture)
B=R/'build';B.mkdir(exist_ok=True)
project=R.parent.parent
lld=os.environ.get('LLD') or shutil.which('ld.lld')
if not lld:raise SystemExit('Set LLD to a RISC-V-capable LLVM linker, or install ld.lld on PATH.')
scalar=[K/f'scalar{i}.c' for i in range(3,7)];fast=[K/f'rvv{i}.c' for i in range(3,7)];fixed=[K/f'frozen_rvv{i}.c' for i in range(3,7)]
cmd=['clang-18','--target=riscv64-unknown-elf','-march=rv64gcv_zba_zbb','-mabi=lp64d','-mcmodel=medany','-msmall-data-limit=0','-O3','-ffreestanding','-fno-builtin','-DBARE','-nostdlib','--ld-path='+lld,'-Wl,-T,'+str(K/'rvv.ld'),'-I',str(K),'-I',str(S),str(K/'start.S'),str(K/'runtime.c'),str(S/'revision_selftest.c'),*map(str,scalar+fast+fixed),'-o',str(B/'revision-selftest.elf')]
result=subprocess.run(cmd,capture_output=True,text=True)
(B/'build.log').write_text(result.stdout+result.stderr)
(B/'build-manifest.json').write_text(json.dumps({'command':cmd,'returncode':result.returncode,'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(S.rglob('*')) if p.is_file()},'scope':'validation only; no physical timing'},indent=2)+'\n')
print(result.stderr);print('Build returncode',result.returncode)
raise SystemExit(result.returncode)
