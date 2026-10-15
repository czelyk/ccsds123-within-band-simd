from pathlib import Path
import subprocess,json,os
R=Path(__file__).resolve().parent;O=R/'src/reference_kernels'
sources=[R/'src/native_bip_capture.c',R/'src/baseline_regression.c']+[O/f'{typ}{c}.c' for typ in ('scalar','avx','frozen') for c in range(3,7)]
cmd=['clang-18','-O1','-g','-march=native','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I',str(O),'-I',str(R/'src'),*map(str,sources),'-o',str(R/'build/baseline-regression')]
b=subprocess.run(cmd,capture_output=True,text=True);(R/'build/sanitizer-build.log').write_text(b.stdout+b.stderr)
if b.returncode:raise RuntimeError(b.stderr)
r=subprocess.run([str(R/'build/baseline-regression')],capture_output=True,text=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1',UBSAN_OPTIONS='halt_on_error=1'))
(R/'evidence/sanitizer-regression.json').write_text(json.dumps({'build_command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'scope':'differential synthetic regression, not independent full-standard conformance'},indent=2)+'\n')
print(r.stdout);print(r.stderr);raise SystemExit(r.returncode)
