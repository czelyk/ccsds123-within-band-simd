
import os,sys,json,time,subprocess,ctypes as ct,hashlib,struct,statistics,gc,termios
from pathlib import Path
import numpy as np,h5py
os.sched_setaffinity(0,{2})
SRC=Path('outputs/iac2027-vector-compression-kit/src').resolve()
L=ct.CDLL('/lib/x86_64-linux-gnu/libLLVM.so.18.1')
P=ct.c_void_p; I=ct.c_int; U=ct.c_uint64; S=ct.c_char_p
def api(n,r,a):
 f=getattr(L,n);f.restype=r;f.argtypes=a;return f
for n in ('LLVMLinkInMCJIT','LLVMInitializeX86TargetInfo','LLVMInitializeX86Target','LLVMInitializeX86TargetMC','LLVMInitializeX86AsmPrinter','LLVMInitializeX86AsmParser'):api(n,None,[])()
ctx=api('LLVMContextCreate',P,[])()
def compile_ir(code,name):
 r=subprocess.run(['clang-18','-O3','-march=native','-S','-emit-llvm','-x','c','-','-o','-','-I',str(SRC)],input=code.encode(),capture_output=True)
 if r.returncode:raise RuntimeError(r.stderr.decode())
 b=api('LLVMCreateMemoryBufferWithMemoryRangeCopy',P,[S,ct.c_size_t,S])(r.stdout,len(r.stdout),name.encode());m=P();e=S()
 if api('LLVMParseIRInContext',I,[P,P,ct.POINTER(P),ct.POINTER(S)])(ctx,b,ct.byref(m),ct.byref(e)):raise RuntimeError(e.value)
 return m
original=(SRC/'fullbench.c').read_text()
csrc=original[:original.index('#ifndef BARE\nstatic double now')]
csrc=csrc.replace('const uint16_t*cur[8],*prev[8]','const uint16_t*cur[128],*prev[128]')
csrc=csrc.replace('int32_t fixed_weights[8][6];','int32_t fixed_weights[128][6];int group,layout,learn_only;int32_t *endweights;uint64_t *trace;size_t trace_n;')
csrc=csrc.replace('Writer writers[8];Entropy states[8];size_t bits[8];','Writer writers[128];Entropy states[128];size_t bits[128];')
csrc=csrc.replace('int32_t weights[8][6];Entropy states[8];','int32_t weights[128][6];Entropy states[128];')
# Init every component, including inactive spectral components for calibration tables.
csrc=csrc.replace('for(int i=0;i<c;i++)w[i]=0;','for(int i=0;i<6;i++)w[i]=0;')
start=csrc.index('static void prepare_rows')
end=csrc.index('static inline int sum',start)
prep=r'''
static uint64_t tick(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;}
static void trace_row(Frame*f,Writer*bw,int y,int z,int first,int last,uint64_t begin){
 if(!f->trace)return;
 uint64_t*q=f->trace+8*f->trace_n++;
 q[0]=y;q[1]=z;q[2]=first;q[3]=last;q[4]=begin;q[5]=tick();q[6]=bw->p-f->output;q[7]=bw->fill;
}
static void prepare_group(Frame*f,int y,int first,int lanes){
 for(int z=first;z<first+lanes;z++){
  f->cur[z]=f->ring+((size_t)2*z+(y&1))*f->width;
  f->prev[z]=f->ring+((size_t)2*z+((y+1)&1))*f->width;
 }
 if(f->layout){
  for(int x=0;x<f->width;x++)for(int z=first;z<first+lanes;z++)
   ((uint16_t*)f->cur[z])[x]=f->raw[((size_t)y*f->width+x)*f->bands+z];
 }else{
  for(int z=first;z<first+lanes;z++)memcpy((uint16_t*)f->cur[z],f->raw+((size_t)y*f->bands+z)*f->width,f->width*2);
 }
 f->received_rows+=lanes;
}
static void prepare_rows(Frame*f,int y,int arriving_band){
 if(f->bil){prepare_group(f,y,arriving_band<0?0:arriving_band,arriving_band<0?f->bands:1);return;}
 for(int z=0;z<f->bands;z++){f->cur[z]=f->raw+z*f->n+(size_t)y*f->width;f->prev[z]=y?f->cur[z]-f->width:f->cur[z];}
}
'''
csrc=csrc[:start]+prep+csrc[end:]
csrc=csrc.replace('encode(bw,e,mapped(f->cur[z][x],p),t);','if(!f->learn_only)encode(bw,e,mapped(f->cur[z][x],p),t);')
# Replace only the inter-band outer execution policy. Dot/update code is retained.
bstart=csrc.index('static void band_parallel(Frame*f,Writer*writers,Entropy*states)',csrc.index('#else\n/* Conventional SIMD'))
bend=csrc.index('\n}\n#endif',bstart)+2
old=csrc[bstart:bend]
mid=old[old.index('        int x0=!y;'):old.rfind('    }\n    (void)zero;')]
mid=mid.replace('for(int x=x0;x<f->width;x++)for(int z=0;z<8;z++){','for(int x=x0;x<f->width;x++)for(int lane=0;lane<8;lane++){\n            int z=zbase+lane;')
mid=mid.replace('if(z<f->bands)sigma=local_values(f,z,x,y,u);','if(lane<lanes)sigma=local_values(f,z,x,y,u);')
mid=mid.replace('(7*(size_t)x+i)*8+z','(7*(size_t)x+i)*8+lane').replace('(7*(size_t)x+6)*8+z','(7*(size_t)x+6)*8+lane')
mid=mid.replace('for(int z=0;z<f->bands;z++){f->predictions[z*f->width+x]=pp[z];actual[z]=2*f->cur[z][x];}','for(int lane=0;lane<lanes;lane++){int z=zbase+lane;f->predictions[lane*f->width+x]=pp[lane];actual[lane]=2*f->cur[z][x];}')
mid=mid.replace('for(int z=0;z<f->bands;z++){\n            Writer*dest=', 'for(int z=zbase;z<zbase+lanes;z++){\n            Writer*dest=')
mid=mid.replace('f->predictions[z*f->width+x]','f->predictions[(z-zbase)*f->width+x]')
mid=mid.replace('if(f->bil&&!y&&!z)f->first_row_after_received=f->received_rows;','if(f->bil&&!y&&!z)f->first_row_after_received=f->received_rows;\n            trace_row(f,dest,y,z,zbase,zbase+lanes,begin);')
band=r'''
static void band_parallel(Frame*f,Writer*writers,Entropy*states){
 int32_t wi[6][136]={{0}};
 for(int z=0;z<f->bands;z++)for(int i=3;i<3+(z<3?z:3);i++)wi[i][z]=i==3?458752:wi[i-1][z]/8;
 for(int y=0;y<f->height;y++)for(int zbase=0;zbase<f->bands;zbase+=f->group){
  int lanes=f->bands-zbase;if(lanes>f->group)lanes=f->group;
  uint64_t begin=f->trace?tick():0;
  prepare_group(f,y,zbase,lanes);
  __m256i weights[6],zero=_mm256_setzero_si256(),one=_mm256_set1_epi32(1),low=_mm256_set1_epi32(-2097152),high=_mm256_set1_epi32(2097151);
  for(int i=0;i<6;i++)weights[i]=_mm256_loadu_si256((void*)(wi[i]+zbase));
'''+mid+r'''
  for(int i=0;i<6;i++){int32_t tmp[8];_mm256_storeu_si256((void*)tmp,weights[i]);for(int lane=0;lane<lanes;lane++)wi[i][zbase+lane]=tmp[lane];}
 }
}
'''
csrc=csrc[:bstart]+band+csrc[bend:]
# Per-band traces and predictor-only calibration; no new codec mode.
needle='int z=f->bil?inner:outer,y=f->bil?outer:inner;\n        prepare_rows(f,y,z);'
assert needle in csrc
csrc=csrc.replace(needle,'int z=f->bil?inner:outer,y=f->bil?outer:inner;\n        uint64_t begin=f->trace?tick():0;\n        prepare_rows(f,y,z);')
csrc=csrc.replace('if(!y)encode(&bw,states+z,','if(!f->learn_only&&!y)encode(&bw,states+z,')
csrc=csrc.replace('if(variant==4)for(int i=0;i<c;i++)','if(variant==4||variant==6)for(int i=0;i<c;i++)')
needle='if(variant==4)fixed_kernels[c-3](&b,weights[z],counts);else'
assert needle in csrc
csrc=csrc.replace(needle,'''if(variant==6){for(int j=0;j<len;j++){int64_t d=(int64_t)b.sigma[j]*2048+4096;for(int i=0;i<c;i++)d+=(int64_t)b.u[i][j]*weights[z][i];b.output[j]=clamp(d>>12,0,131071);}}else
            if(variant==4)fixed_kernels[c-3](&b,weights[z],counts);else''')
# Final trace hook occurs in the non-band loop only.
needle='if(f->bil&&!y&&!z)f->first_row_after_received=f->received_rows;\n    }\n    if(bw.fill)'
assert needle in csrc
csrc=csrc.replace(needle,'''if(f->bil&&!y&&!z)f->first_row_after_received=f->received_rows;
        trace_row(f,&bw,y,z,z,z+1,begin);
    }
    if(f->endweights)memcpy(f->endweights,weights,(size_t)f->bands*6*sizeof(int32_t));
    if(f->learn_only)return 0;
    if(bw.fill)''')
entry=r'''
void* make_context(uint16_t*raw,int width,int height,int bands,int local,int nu,int layout){
 if(width<2||height<1||bands<1||bands>128)return 0;
 Frame*f=calloc(1,sizeof(Frame));f->raw=raw;f->width=width;f->height=height;f->bands=bands;f->local=local;f->nu_max=nu;f->n=(size_t)width*height;f->bil=1;f->layout=layout;
 f->scratch=aligned_alloc(64,((40*width+63)/64)*64);f->band_scratch=calloc((size_t)7*width*8,4);f->predictions=malloc((size_t)width*8*4);f->ring=calloc((size_t)2*width*bands,2);
 return f;
}
uint64_t compute(void*v,int variant,int group,int learn_lines,int32_t*weights,uint8_t*out,uint64_t*counts,uint64_t*trace){
 Frame*f=v;int full_height=(int)(f->n/f->width);f->height=learn_lines?learn_lines:full_height;f->learn_only=learn_lines!=0;f->output=out;f->group=group;f->trace=trace;f->trace_n=0;f->endweights=learn_lines?weights:0;
 if(variant==4||variant==6)for(int z=0;z<f->bands;z++)for(int i=0;i<6;i++)f->fixed_weights[z][i]=weights[z*6+i];
 Counts c={0};size_t n=run(f,variant,&c);counts[0]=c.accepted;counts[1]=c.rejected;counts[2]=f->first_row_after_received;counts[3]=f->trace_n;
 f->height=full_height;return n;
}
void free_context(void*v){Frame*f=v;free(f->scratch);free(f->band_scratch);free(f->predictions);free(f->ring);free(f);}
'''
csrc+=entry

get=api('LLVMGetFunctionAddress',U,[P,S])
csrc2=csrc.replace('f->endweights=learn_lines?weights:0;','f->endweights=(learn_lines||variant==0)?weights:0;')

bs=csrc2.index('static void band_parallel(');be=csrc2.index('\n#endif',bs)
compact=csrc2[bs:be].replace('static void band_parallel(','static void band_parallel_compact(',1)
start=compact.index('for(int x=x0;x<f->width;x++)for(int lane=0;lane<8;lane++){')
end=compact.index('for(int x=x0;x<f->width;x++){',start)
prep=compact[start:end]
compact=compact[:start]+compact[end:]
inner=prep[prep.index('for(int lane=0;lane<8;lane++){'):]
inner=inner.replace('f->band_scratch[(7*(size_t)x+i)*8+lane]','features[i*8+lane]').replace('f->band_scratch[(7*(size_t)x+6)*8+lane]','features[6*8+lane]')
compact=compact.replace('for(int x=x0;x<f->width;x++){','for(int x=x0;x<f->width;x++){\nint32_t features[7*8];\n'+inner,1)
compact=compact.replace('f->band_scratch+(7*(size_t)x+i)*8','features+i*8').replace('f->band_scratch+(7*(size_t)x+6)*8','features+6*8')
assert 'band_scratch' not in compact
csrc3=csrc2[:be]+'\n'+compact+csrc2[be:]
csrc3=csrc3.replace('if(variant==3){','if(variant==3||variant==7){')
csrc3=csrc3.replace('band_parallel(f,&bw,states);','if(variant==7)band_parallel_compact(f,&bw,states);else band_parallel(f,&bw,states);')
csrc3=csrc3.replace('band_parallel(f,writers,states);','if(variant==7)band_parallel_compact(f,writers,states);else band_parallel(f,writers,states);')
mm=compile_ir(csrc3,'compact_band')
for typ in ('scalar','avx','frozen'):
 for k in range(3,7):assert api('LLVMLinkModules2',I,[P,P])(mm,compile_ir((SRC/f'{typ}{k}.c').read_text(),f'{typ}{k}_v3'))==0
ee3=P();err=S();assert api('LLVMCreateExecutionEngineForModule',I,[ct.POINTER(P),P,ct.POINTER(S)])(ct.byref(ee3),mm,ct.byref(err))==0,err.value
create=ct.CFUNCTYPE(P,P,I,I,I,I,I,I)(get(ee3,b'make_context'))
compute=ct.CFUNCTYPE(U,P,I,I,I,P,P,P,P)(get(ee3,b'compute'))
destroy=ct.CFUNCTYPE(None,P)(get(ee3,b'free_context'))
print(json.dumps({'kind':'compact-source','sha256':hashlib.sha256(csrc3.encode()).hexdigest(),'new_variant':7,'change':'conventional across-band SIMD constructs 7x8 int features on stack per x; retains per-group prediction-row buffer and byte order; no change to proposed algorithm or scalar kernels','additional_scratch_bytes_excluding_prediction_row':224}),flush=True)

def run_native(data,local=3,layout=0,variants=((0,1),(1,1),(2,1),(5,1),(3,1),(3,2),(3,4),(3,8)),weights=None,trials=3,trace_variant=None):
 h,w,z=data.shape;raw=np.ascontiguousarray(data if layout else data.transpose(0,2,1));context=create(raw.ctypes.data,w,h,z,local,9,layout);assert context
 out=np.empty(data.size*6+16,dtype=np.uint8);counts=np.zeros(4,dtype=np.uint64);tab=np.zeros((z,6),dtype=np.int32) if weights is None else np.ascontiguousarray(weights,dtype=np.int32)
 ref=6 if weights is not None else 0
 n=compute(context,ref,1,0,tab.ctypes.data,out.ctypes.data,counts.ctypes.data,0)
 base=out[:n].tobytes();digest=hashlib.sha256(base).hexdigest();records=[];traces={}
 for trial in range(trials):
  order=list(variants[trial%len(variants):]+variants[:trial%len(variants)])
  for v,g in order:
   t=time.perf_counter_ns();n=compute(context,v,g,0,tab.ctypes.data,out.ctypes.data,counts.ctypes.data,0);elapsed=time.perf_counter_ns()-t
   assert out[:n].tobytes()==base,(v,g,'body mismatch')
   records.append({'trial':trial,'variant':v,'group':g,'ns_sample':elapsed/data.size,'bytes':int(n),'accepted':int(counts[0]),'rejected':int(counts[1]),'first_row_after_received':int(counts[2])})
 if trace_variant is not None:
  v,g=trace_variant;trace=np.empty((h*z,8),dtype=np.uint64);n=compute(context,v,g,0,tab.ctypes.data,out.ctypes.data,counts.ctypes.data,trace.ctypes.data)
  assert out[:n].tobytes()==base
  traces[(v,g)]={'trace':trace[:counts[3]].copy(),'bytes':int(n)}
 destroy(context)
 return records,base,traces
def summarize(records):
 return {f"{v}:{g}":{'median_ns':statistics.median(x['ns_sample'] for x in records if (x['variant'],x['group'])==(v,g)),
  'trials_ns':[x['ns_sample'] for x in records if (x['variant'],x['group'])==(v,g)],
  'accepted':next(x['accepted'] for x in records if (x['variant'],x['group'])==(v,g)),
  'rejected':next(x['rejected'] for x in records if (x['variant'],x['group'])==(v,g))}
 for v,g in dict.fromkeys((x['variant'],x['group']) for x in records)}

inputs=json.loads(Path('work/ccsds_followup/selected_hypso_inputs.json').read_text())

compact_finish={}
name=inputs[3]['filename']
with h5py.File(Path('work/ccsds_followup/raw')/name,'r') as f:data=f['products/dn'][:]
r,b,_=run_native(data,local=0,layout=1,variants=((7,2),(7,4),(7,8)),trials=3)
print(json.dumps({'kind':'compact-band-BIP-finished','file':name,'local':0,'body_bytes':len(b),'body_sha256':hashlib.sha256(b).hexdigest(),'methods':summarize(r),'all_bodies_equal':True}),flush=True)
del data,b;gc.collect()
name=inputs[1]['filename']
with h5py.File(Path('work/ccsds_followup/raw')/name,'r') as f:data=f['products/dn'][:]
for layout in (1,0):
 r,b,tr=run_native(data,local=3,layout=layout,variants=((0,1),(2,1),(7,2),(7,4),(7,8)),trials=3,trace_variant=(7,8))
 q={'kind':'paired-compact-comparison','file':name,'local':3,'layout':'BIP' if layout else 'BIL','nu_max':9,'body_bytes':len(b),'body_sha256':hashlib.sha256(b).hexdigest(),'methods':summarize(r),'all_bodies_equal':True}
 compact_finish[layout]=q;print(json.dumps(q),flush=True)
 a=tr[(7,8)]['trace'];j=int(np.searchsorted(a[:,6],1024));row=a[j]
 print(json.dumps({'kind':'compact-band-trace','layout':layout,'group':8,'first1024_body_row':j,'first_input_rows':8,'first_row_finish_us':(int(row[5])-int(row[4]))/1000,'trace_sha256':hashlib.sha256(a.tobytes()).hexdigest()}),flush=True)
import types
create_saved=create
def create4(ptr,w,h,z,local,nu,layout):return create_saved(ptr,w,h,z,local,4,layout)
run4=types.FunctionType(run_native.__code__,dict(run_native.__globals__,create=create4),'run4',run_native.__defaults__)
r,b,_=run4(data,local=3,layout=1,variants=((0,1),(2,1),(7,2),(7,4),(7,8)),trials=3)
print(json.dumps({'kind':'paired-compact-nu4','file':name,'local':3,'layout':'BIP','nu_max':4,'body_bytes':len(b),'body_sha256':hashlib.sha256(b).hexdigest(),'methods':summarize(r),'all_bodies_equal':True}),flush=True)
print('FINAL_PAIRED_COMPLETE',flush=True)

