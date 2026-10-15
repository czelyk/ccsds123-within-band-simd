"""Build a bounded new comparator without changing the proposal or old kit."""
from pathlib import Path
import subprocess,json,hashlib,platform,shutil
ROOT=Path(__file__).resolve().parent
ORIG=ROOT/'src/reference_kernels'
s=(ROOT/'src/followup_host.c').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='526aac8a93ca5b91e502e018d8252dd8bcfe0aaf854f6177f5a621dce9b58bf8'
s=s.replace('static size_t run(Frame*f,int variant,Counts*counts){','#include "tap_baseline.inc"\nstatic size_t run(Frame*f,int variant,Counts*counts){')
s=s.replace('if(variant==0||variant==5){(variant==0?fused[c-3]:eager[c-3])','if(variant==0||variant==5||variant==8){(variant==8?taps[c-3]:variant==0?fused[c-3]:eager[c-3])')
assert 'variant==8?taps' in s
(ROOT/'src/tap_host.c').write_text(s)
sources=[ROOT/'src/tap_host.c']
for typ in ('scalar','avx','frozen'):
    for c in range(3,7):sources.append(ORIG/f'{typ}{c}.c')
build=ROOT/'build';build.mkdir(exist_ok=True)
command=['clang-18','-O3','-march=native','-shared','-fPIC','-I',str(ORIG),'-I',str(ROOT/'src'),*map(str,sources),'-o',str(build/'libreassessment.so')]
r=subprocess.run(command,capture_output=True,text=True)
(build/'build.log').write_text(r.stdout+r.stderr)
manifest={'command':command,'returncode':r.returncode,'platform':platform.platform(),'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'src/tap_baseline.inc']}}
(build/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'returncode':r.returncode,'source_sha256':manifest['sources'][str(sources[0])]}))
if r.returncode:raise SystemExit(r.returncode)
