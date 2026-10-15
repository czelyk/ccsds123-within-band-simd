"""Stronger fixed baseline for the stated lossless profile; separate campaign."""
from pathlib import Path
import os,sys,json,ctypes as ct,hashlib,statistics,time,gc,ast,contextlib,io,subprocess
import numpy as np
R=Path(__file__).resolve().parent;S=R/'src';K=S/'reference_kernels'
os.sched_setaffinity(0,{int(os.environ.get('CCSDS_CPU','2'))})
sys.path.insert(0,os.environ.get('CCSDS_NTNU_DIR',str(R.parent.parent/'work/cycle13/ntnu')))
from ccsds123_i2_hlm import header as hd
from ccsds123_i2_hlm.constants import ImageConstants
from ccsds123_i2_hlm.predictor import Predictor
from ccsds123_i2_hlm.sa_encoder import SampleAdaptiveEncoder
# Reuse only the header function, without executing the experiment or opening
# its output stream. Historical measurements must never be overwritten.
tree=ast.parse((R/'run_landsat_pilot.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='header')
exec(compile(ast.Module(body=[node],type_ignores=[]),'reused_header','exec'))
s=(S/'pilot_host.c').read_text();s=s.replace('b.sigma[j]*2048+4096','b.sigma[j]*4096+8192').replace('clamp(d>>12,0,131071)','clamp(d>>13,0,131071)')
(S/'fixed12_host.c').write_text(s)
frozen=[]
for c in range(3,7):
 p=S/f'fixed12_{c}.c';p.write_text((K/f'frozen{c}.c').read_text().replace('#define OMEGA 11','#define OMEGA 12'));frozen.append(p)
sources=[S/'fixed12_host.c']+[K/f'{typ}{c}.c' for typ in ('scalar','avx') for c in range(3,7)]+frozen
cmd=['clang-18','-O3','-march=native','-shared','-fPIC','-I',str(K),'-I',str(S),*map(str,sources),'-o',str(R/'build/libfixed12.so')]
b=subprocess.run(cmd,capture_output=True,text=True);(R/'build/fixed12-build.log').write_text(b.stdout+b.stderr)
(R/'build/fixed12-build-manifest.json').write_text(json.dumps({'command':cmd,'returncode':b.returncode,'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}},indent=2)+'\n')
if b.returncode:raise RuntimeError(b.stderr)
lib=ct.CDLL(str(R/'build/libfixed12.so'));P=ct.c_void_p;I=ct.c_int
lib.make_context.argtypes=[P,I,I,I,I,I,I];lib.make_context.restype=P;lib.compute.argtypes=[P,I,I,I,P,P,P,P];lib.compute.restype=ct.c_uint64;lib.free_context.argtypes=[P]
stream=(R/'evidence/fixed12-followup.jsonl').open('w',buffering=1)
def emit(x):stream.write(json.dumps(x)+'\n');print(json.dumps(x),flush=True)
def q12(shape,local,table=None):
 q=header(shape,local);q.set_weight_component_resolution(12);q.set_weight_update_initial_parameter(9);q.set_weight_update_final_parameter(9)
 q.weight_exponent_offset_flag=hd.WeightExponentOffsetFlag.NOT_ALL_ZERO;q.weight_exponent_offset_value=5;q.set_weight_exponent_offset_table_array_to_default();q.weight_exponent_offset_table_flag=hd.WeightExponentOffsetTableFlag.INCLUDED
 if table is not None:q.weight_init_method=hd.WeightInitMethod.CUSTOM;q.weight_init_resolution=15;q.weight_init_table_flag=hd.WeightInitTableFlag.INCLUDED;q.weight_init_table=table.astype(np.int64)
 q.check_legal_config();return q
def default12():
 w=np.zeros((7,6),np.int32)
 for z in range(7):
  for i in range(3,3+min(z,3)):w[z,i]=3584 if i==3 else w[z,i-1]//8
 return w
def context(data,local,nu):
 h,w,z=data.shape;c=lib.make_context(data.ctypes.data,w,h,z,local,nu,1);assert c;return c
def call(c,v,table,out,counts,lines=0):return lib.compute(c,v,1,lines,table.ctypes.data,out.ctypes.data,counts.ctypes.data,0)
u=np.arange(-4*65535,4*65535+1,dtype=np.int64)
assert np.all((((u>>18)+1)>>1)==0)
emit({'kind':'arithmetic-bound','differences_checked':len(u),'Omega':12,'constant_rho_with_offsets5':18,'all_updates_zero':True,'Omega13_counterexample_u':131072,'Omega13_counterexample_update':((131072>>17)+1)>>1,'scope':'lossless zero-damping differences only; straightforward bound, not a claimed new contribution'})
D=Path(os.environ.get('LANDSAT_DATA_DIR',str(R.parent.parent/'work/ccsds_revision_landsat')))
items=json.loads((R/'evidence/landsat8-selection.json').read_text())['selected'];old=[json.loads(l) for l in (R/'evidence/landsat-pilot.jsonl').read_text().splitlines()]
summaries={(x['file'],x['local'],x['nu_max']):x for x in old if x['kind']=='summary'}
priors={}
source=np.ascontiguousarray(np.memmap(D/items[0]['filename'],mode='r',dtype='<u2',shape=(7,4096,4096)).transpose(1,2,0))
for local,nu in ((3,9),(0,9),(3,4)):
 c=context(source,local,nu);w=np.zeros((7,6),np.int32);counts=np.zeros(4,np.uint64);out=np.empty(16,np.uint8);start=time.perf_counter_ns();call(c,0,w,out,counts,4096);seconds=(time.perf_counter_ns()-start)/1e9
 priors[(local,nu)]=np.clip((w.astype(np.int64)+64)>>7,-16384,16383).astype(np.int32)
 emit({'kind':'retrospective-training','file':items[0]['filename'],'local':local,'nu_max':nu,'seconds':seconds,'Omega19_final_weights':w.tolist(),'Omega12_weights':priors[(local,nu)].tolist(),'operational_availability_verified':False});lib.free_context(c)
del source;gc.collect()
for index,item in enumerate(items):
 data=np.ascontiguousarray(np.memmap(D/item['filename'],mode='r',dtype='<u2',shape=(7,4096,4096)).transpose(1,2,0))
 for local,nu in ((3,9),(0,9),*(([(3,4)] if index==1 else []))):
  c=context(data,local,nu);out=np.empty(data.size*6+16,np.uint8);counts=np.zeros(4,np.uint64)
  for calibration,table in [('default',default12())]+([('earlier-acquisition-retrospective',priors[(local,nu)].copy())] if index else []):
   custom=table if calibration!='default' else None
   # Independent checks cover both local sums, default/custom tables and the
   # preselected secondary calibration on the first held-out acquisition.
   if index==1:
    prefix=np.ascontiguousarray(data[:2]);q=q12(prefix.shape,local,custom);p=Predictor(q,ImageConstants(q),prefix.astype(np.int64))
    with contextlib.redirect_stdout(io.StringIO()):p.run_predictor()
    for z in range(7):assert np.all(p.weight_vector[:,:,z,:3+min(z,3)]==table[z,:3+min(z,3)])
    e=SampleAdaptiveEncoder(q,ImageConstants(q),p.get_predictor_output())
    with contextlib.redirect_stdout(io.StringIO()):e.run_encoder()
    cc=context(prefix,local,nu);nn=call(cc,6,table,out,counts);gold=e.bitstream.tobytes();assert gold==out[:nn].tobytes();lib.free_context(cc)
    emit({'kind':'independent-prefix','file':item['filename'],'local':local,'nu_max_training':nu,'calibration':calibration,'shape':list(prefix.shape),'body_bytes':nn,'sha256':hashlib.sha256(gold).hexdigest(),'all_active_weights_constant':True,'pass':True});del p,e,prefix;gc.collect()
   nn=call(c,6,table,out,counts);gold=out[:nn].tobytes();trials=[]
   if calibration=='default':
    expected=next(x for x in old if x['kind']=='fixed-summary' and x['file']==item['filename'] and x['local']==local and x['nu_max']==nu and x['calibration']=='default')
    assert hashlib.sha256(gold).hexdigest()==expected['sha256']
    nv=call(c,4,table,out,counts);assert nv==nn and out[:nv].tobytes()==gold
    head=q12(data.shape,local).get_header_bitstreams()[0].tobytes();assert nn+len(head)==expected['total_bytes']
    emit({'kind':'default-identity','file':item['filename'],'local':local,'nu_max_training':nu,'Omega':12,'body_bytes':nn,'header_bytes':len(head),'body_sha256':expected['sha256'],'matches_Omega11_body_and_size':True,'timing_repeated':False,'reason':'Default weights double exactly; normalized prediction is unchanged'})
    continue
   for trial in range(3):
    for v in ((4,6) if trial%2==0 else (6,4)):
     start=time.perf_counter_ns();n=call(c,v,table,out,counts);end=time.perf_counter_ns();assert out[:n].tobytes()==gold
     row={'kind':'timing','file':item['filename'],'local':local,'nu_max_training':nu,'calibration':calibration,'variant':v,'trial':trial,'ns_sample':(end-start)/data.size};trials.append(row);stream.write(json.dumps(row)+'\n')
   head=q12(data.shape,local,custom).get_header_bitstreams()[0].tobytes();adaptive=summaries[(item['filename'],local,nu)]['total_bytes'];total=nn+len(head)
   emit({'kind':'summary','file':item['filename'],'role':'training-acquisition' if not index else 'held-out-acquisition','local':local,'nu_max_training':nu,'calibration':calibration,'Omega':12,'body_bytes':nn,'header_bytes':len(head),'total_bytes':total,'size_change_percent':100*(total/adaptive-1),'methods_ns':{str(v):statistics.median(x['ns_sample'] for x in trials if x['variant']==v) for v in (4,6)},'body_sha256':hashlib.sha256(gold).hexdigest(),'precision_confounded_with_adaptation':True,'campaign':'separate from main pilot; no paired cross-campaign timing inference'})
  lib.free_context(c);del out;gc.collect()
 del data;gc.collect()
stream.close();print('FIXED12_COMPLETE',flush=True)
