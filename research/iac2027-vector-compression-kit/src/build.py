"""Build exploratory host tests or RVV bare-metal functional tests."""
from pathlib import Path
import argparse,subprocess,os,shutil,json
P=Path(__file__).resolve().parent
a=argparse.ArgumentParser();a.add_argument('target',choices=['host','rvv','rvv-native','rvv-linux-cross']);a.add_argument('--lld');a.add_argument('--renode');a.add_argument('--sysroot');a.add_argument('--gcc-dir');args=a.parse_args()
def run(cmd):
    print(' '.join(map(str,cmd)),flush=True);subprocess.run(list(map(str,cmd)),check=True)
scalar=[P/f'scalar{i}.c' for i in range(3,7)]
if args.target in ['host','rvv-native','rvv-linux-cross']:
    rv=args.target!='host'
    cc=os.environ.get('CC','clang' if rv else 'gcc')
    base=[cc,'-O3']+(['-march=rv64gcv_zba_zbb','-DRVV_NATIVE'] if rv else ['-march=native'])
    if args.target=='rvv-linux-cross':
        if not all([args.sysroot,args.gcc_dir,args.lld]):raise SystemExit('Pass --sysroot, --gcc-dir and --lld.')
        base+=['--target=riscv64-linux-gnu','-mabi=lp64d','--sysroot='+str(Path(args.sysroot).resolve()),'--gcc-install-dir='+str(Path(args.gcc_dir).resolve()),'--ld-path='+str(Path(args.lld).resolve()),'-static']
    fast=[P/f'{"rvv" if rv else "avx"}{i}.c' for i in range(3,7)]
    fixed=[P/f'{"frozen_rvv" if rv else "frozen"}{i}.c' for i in range(3,7)]
    dest=P/('fullbench_rvv_linux' if args.target=='rvv-linux-cross' else 'fullbench')
    run(base+[P/'fullbench.c']+scalar+fast+fixed+['-o',dest])
    if not rv:run(base+[P/'selftest.c']+scalar+fast+['-o',P/'selftest']);run([P/'selftest'])
else:
    lld=args.lld or shutil.which('ld.lld')
    if not lld:raise SystemExit('Pass --lld with a working RISC-V-capable LLVM linker.')
    fast=[P/f'rvv{i}.c' for i in range(3,7)];fixed=[P/f'frozen_rvv{i}.c' for i in range(3,7)]
    base=[os.environ.get('CLANG','clang-18'),'--target=riscv64-unknown-elf','-march=rv64gcv_zba_zbb','-mabi=lp64d','-mcmodel=medany','-msmall-data-limit=0','-O3','-ffreestanding','-fno-builtin','-DBARE','-nostdlib','--ld-path='+str(Path(lld).resolve()),'-Wl,-T,'+str(P/'rvv.ld')]
    files=sorted(P.glob('frame_*_nu9*.bin'))
    if not files:raise SystemExit('No reference fixtures found.')
    asm=['.section .rodata'];hdr=[]
    for i,f in enumerate(files):
        asm+=['.balign 8',f'.global fixture{i}',f'fixture{i}:',f'.incbin "{f}"'];hdr+=[f'extern const uint8_t fixture{i}[];']
    hdr+=['#define FIXTURE_COUNT '+str(len(files)),'static const uint8_t *fixtures[]={'+','.join('fixture'+str(i) for i in range(len(files)))+'};']
    (P/'bare_fixtures.S').write_text('\n'.join(asm)+'\n');(P/'bare_fixtures.h').write_text('\n'.join(hdr)+'\n')
    run(base+[P/'start.S',P/'runtime.c',P/'selftest.c']+scalar+fast+['-o',P/'selftest.elf'])
    run(base+[P/'start.S',P/'runtime.c',P/'fullbench.c',P/'bare_fixtures.S']+scalar+fast+fixed+['-o',P/'fulltest.elf'])
    report={}
    for length in [128,256,512,1024]:
        for name,seconds in [('selftest',1),('fulltest',24)]:
            status=P/f'{name}_status{length}.bin';script=P/f'{name}{length}.resc'
            script.write_text(f'mach create\nmachine LoadPlatformDescription @{P/"rvv.repl"}\ncpu VectorRegisterLength {length}\ncpu PerformanceInMips 100\nsysbus LoadELF @{P/(name+".elf")}\nemulation RunFor "{seconds}"\ndump_file 0x80000000 64 "{status}"\nquit\n')
            if args.renode:
                import struct
                status.unlink(missing_ok=True)
                r=subprocess.run([args.renode,'--plain','--disable-gui','-P','-1',str(script)],capture_output=True,text=True,timeout=45)
                (P/f'{name}{length}.log').write_text(r.stdout+r.stderr)
                if r.returncode:raise SystemExit(r.stdout+r.stderr)
                values=struct.unpack('<8Q',status.read_bytes());report[f'{name}_{length}']=values
                print(name,length,values,flush=True)
                if values[0]!=0x600dcc53 or not values[1] or values[2] or values[5] or (name=='fulltest' and not values[7]):raise SystemExit('Functional check failed or did not finish.')
    (P/'renode_results.json').write_text(json.dumps(report,indent=2))
