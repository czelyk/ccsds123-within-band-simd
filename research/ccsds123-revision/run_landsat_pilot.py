"""Outcome-independent full-image processed Landsat pilot. No physical claims."""
from pathlib import Path
import os,sys,json,time,ctypes as ct,hashlib,statistics,gc,contextlib,io
import numpy as np
R=Path(__file__).resolve().parent
D=Path(os.environ.get('LANDSAT_DATA_DIR',str(R.parent.parent/'data/landsat')))
sys.path.insert(0,os.environ.get('CCSDS_NTNU_DIR',str(R.parent.parent/'external/ccsds123_issue_2_verification_model')))
from ccsds123_i2_hlm import header as hd
from ccsds123_i2_hlm.constants import ImageConstants
from ccsds123_i2_hlm.predictor import Predictor
from ccsds123_i2_hlm.sa_encoder import SampleAdaptiveEncoder
os.sched_setaffinity(0,{int(os.environ.get('CCSDS_CPU','2'))})
lib=ct.CDLL(str(R/'build/libpilot.so'));P=ct.c_void_p;I=ct.c_int;U=ct.c_uint64
lib.make_context.argtypes=[P,I,I,I,I,I,I];lib.make_context.restype=P
lib.compute.argtypes=[P,I,I,I,P,P,P,P];lib.compute.restype=U;lib.free_context.argtypes=[P]
stream=(R/'evidence/landsat-pilot.jsonl').open('w',buffering=1)
def emit(r):stream.write(json.dumps(r)+'\n');print(json.dumps(r),flush=True)
def header(shape,local,nu=9,order='BIL',weights=None,fixed=False):
 h,w,z=shape;q=hd.Header(f'frame-u16be-{z}x{h}x{w}.raw')
 q.quantizer_fidelity_control_method=hd.QuantizerFidelityControlMethod.LOSSLESS;q.sample_representative_flag=hd.SampleRepresentativeFlag.NOT_INCLUDED
 q.damping_table_array[:]=0;q.damping_offset_table_array[:]=0;q.fixed_damping_value=0;q.fixed_offset_value=0
 q.prediction_mode=hd.PredictionMode.FULL;q.local_sum_type=hd.LocalSumType.NARROW_COLUMN_ORIENTED if local==3 else hd.LocalSumType.WIDE_NEIGHBOR_ORIENTED
 q.set_weight_update_final_parameter(nu);q.sample_encoding_order=hd.SampleEncodingOrder.BI;q.sub_frame_interleaving_depth=z if order=='BIP' else 1;q.entropy_coder_type=hd.EntropyCoderType.SAMPLE_ADAPTIVE
 q.set_unary_length_limit(32);q.set_initial_count_exponent(3);q.set_rescaling_counter_size(8);q.set_accumulator_init_constant(2);q.set_accumulator_init_table_to_default()
 if fixed:
  q.set_weight_component_resolution(11);q.set_weight_update_initial_parameter(9);q.set_weight_update_final_parameter(9)
  q.weight_exponent_offset_flag=hd.WeightExponentOffsetFlag.NOT_ALL_ZERO;q.weight_exponent_offset_value=5;q.set_weight_exponent_offset_table_array_to_default();q.weight_exponent_offset_table_flag=hd.WeightExponentOffsetTableFlag.INCLUDED
  if weights is not None:q.weight_init_method=hd.WeightInitMethod.CUSTOM;q.weight_init_resolution=14;q.weight_init_table_flag=hd.WeightInitTableFlag.INCLUDED;q.weight_init_table=weights.astype(np.int64)
 q.check_legal_config();return q
def oracle(data,local,nu,order,weights=None,fixed=False):
 q=header(data.shape,local,nu,order,weights,fixed);p=Predictor(q,ImageConstants(q),data.astype(np.int64))
 with contextlib.redirect_stdout(io.StringIO()):p.run_predictor()
 e=SampleAdaptiveEncoder(q,ImageConstants(q),p.get_predictor_output())
 with contextlib.redirect_stdout(io.StringIO()):e.run_encoder()
 return e.bitstream.tobytes(),q.get_header_bitstreams()[0].tobytes()
def context(data,local,nu):
 h,w,z=data.shape;c=lib.make_context(data.ctypes.data,w,h,z,local,nu,1);assert c;return c
def call(c,v,g,weights,out,counts,lines=0):return lib.compute(c,v,g,lines,weights.ctypes.data,out.ctypes.data,counts.ctypes.data,0)
def independent_prefix(data,name,nu=9):
 data=np.ascontiguousarray(data[:2]);c=context(data,3,nu);out=np.empty(data.size*6+16,np.uint8);w=np.zeros((7,6),np.int32);counts=np.zeros(4,np.uint64)
 for order,v in (('BIL',0),('BIP',11)):
  gold,head=oracle(data,3,nu,order);n=call(c,v,1,w,out,counts);assert gold==out[:n].tobytes(),(name,nu,order,'independent mismatch')
  emit({'kind':'independent-prefix','file':name,'shape':list(data.shape),'local':3,'nu_max':nu,'order':order,'body_bytes':n,'sha256':hashlib.sha256(gold).hexdigest(),'header_hex':head.hex(),'pass':True})
 # Default fixed profile is independently checked; custom tables have separate
 # historical correctness evidence and are checked against scalar below.
 if nu==9:
  tab=defaults();gold,head=oracle(data,3,nu,'BIL',None,True);n=call(c,6,1,tab,out,counts);assert gold==out[:n].tobytes()
  emit({'kind':'independent-fixed-prefix','file':name,'shape':list(data.shape),'body_bytes':n,'sha256':hashlib.sha256(gold).hexdigest(),'header_hex':head.hex(),'pass':True})
 lib.free_context(c)
def defaults():
 t=np.zeros((7,6),np.int32)
 for z in range(7):
  for i in range(3,3+min(z,3)):t[z,i]=1792 if i==3 else t[z,i-1]//8
 return t
priors={}
def run(data,name,local,nu,index,secondary=False):
 label={'file':name,'local':local,'nu_max':nu,'shape':list(data.shape),'role':'training-acquisition' if not index else 'held-out-acquisition','secondary':secondary,'layout':'resident BIP replay from BSQ product; transpose excluded'}
 c=context(data,local,nu);out=np.empty(data.size*6+16,np.uint8);w=np.zeros((7,6),np.int32);counts=np.zeros(4,np.uint64)
 n=call(c,0,1,w,out,counts);bil=out[:n].tobytes();bilsha=hashlib.sha256(bil).hexdigest();nb=call(c,11,1,w,out,counts);assert nb==n;bip=out[:nb].tobytes();bipsha=hashlib.sha256(bip).hexdigest()
 methods=((0,1),(2,1),(7,8),(8,1),(9,4),(9,8),(11,1));trials=[]
 for trial in range(3):
  for v,g in methods[trial:]+methods[:trial]:
   start=time.perf_counter_ns();nn=call(c,v,g,w,out,counts);end=time.perf_counter_ns()
   assert nn==n and out[:nn].tobytes()==(bip if v in (9,11) else bil),(label,v,g,'full body mismatch')
   row=dict(label,kind='timing',trial=trial,variant=v,group=g,ns_sample=(end-start)/data.size,body_bytes=nn,accepted=int(counts[0]),rejected=int(counts[1]));trials.append(row);stream.write(json.dumps(row)+'\n')
 med={f'{v}:{g}':statistics.median(r['ns_sample'] for r in trials if (r['variant'],r['group'])==(v,g)) for v,g in methods}
 head=header(data.shape,local,nu).get_header_bitstreams()[0].tobytes();adaptive_total=n+len(head)
 emit(dict(label,kind='summary',methods_ns=med,body_bytes=n,header_bytes=len(head),total_bytes=adaptive_total,BIL_sha256=bilsha,BIP_sha256=bipsha,trials=3,all_outputs_match_order_reference=True))
 if not index:
  start=time.perf_counter_ns();call(c,0,1,w,out,counts,lines=data.shape[0]);seconds=(time.perf_counter_ns()-start)/1e9
  priors[(local,nu)]=np.clip((w.astype(np.int64)+128)>>8,-8192,8191).astype(np.int32)
  emit(dict(label,kind='retrospective-training',seconds=seconds,weights=priors[(local,nu)].tolist(),operational_table_availability_verified=False))
 choices=[('default',defaults())]
 if index:choices.append(('earlier-acquisition-retrospective',priors[(local,nu)].copy()))
 for calibration,table in choices:
  fixed_trials=[];gold_n=call(c,6,1,table,out,counts);gold=out[:gold_n].tobytes()
  for trial in range(3):
   for v in ((4,6) if trial%2==0 else (6,4)):
    start=time.perf_counter_ns();nn=call(c,v,1,table,out,counts);end=time.perf_counter_ns();assert out[:nn].tobytes()==gold
    row=dict(label,kind='fixed-timing',calibration=calibration,variant=v,trial=trial,ns_sample=(end-start)/data.size,body_bytes=nn);fixed_trials.append(row);stream.write(json.dumps(row)+'\n')
  fh=header(data.shape,local,nu,weights=table if calibration!='default' else None,fixed=True).get_header_bitstreams()[0].tobytes();total=gold_n+len(fh)
  emit(dict(label,kind='fixed-summary',calibration=calibration,body_bytes=gold_n,header_bytes=len(fh),total_bytes=total,size_change_percent=100*(total/adaptive_total-1),methods_ns={str(v):statistics.median(r['ns_sample'] for r in fixed_trials if r['variant']==v) for v in (4,6)},sha256=hashlib.sha256(gold).hexdigest(),precision_confounded_with_adaptation=True))
 if not secondary:
  for splits in (2,4,8):
   total=0;seconds=0.;body_hashes=[]
   for stripe in np.split(data,splits,axis=0):
    cc=context(stripe,local,nu);start=time.perf_counter_ns();nn=call(cc,0,1,w,out,counts);seconds+=(time.perf_counter_ns()-start)/1e9
    hh=header(stripe.shape,local,nu).get_header_bitstreams()[0].tobytes();total+=nn+len(hh);body_hashes.append(hashlib.sha256(out[:nn].tobytes()).hexdigest());lib.free_context(cc)
   emit(dict(label,kind='independent-stripe-reset',stripes=splits,total_bytes=total,size_change_percent=100*(total/adaptive_total-1),sequential_encode_seconds=seconds,body_hashes=body_hashes,parallel_execution_measured=False))
 lib.free_context(c);del out,bil,bip;gc.collect()
emit({'kind':'environment','cpu':'i7-12700H','affinity':sorted(os.sched_getaffinity(0)),'compiler':'Clang18 O3 march=native','frequency_controlled':False,'physical_RVV':False,'scope':'processed L1 resident replay; no measured sensor arrival, DMA, file I/O, header work or telemetry in timing'})
items=json.loads((R/'evidence/landsat8-selection.json').read_text())['selected']
for index,item in enumerate(items):
 path=D/item['filename']
 if not path.exists():raise SystemExit('Input missing: '+str(path)+'. Run fetch_landsat.py first or set LANDSAT_DATA_DIR.')
 assert path.stat().st_size==7*4096*4096*2
 bsq=np.memmap(path,mode='r',dtype='<u2',shape=(7,4096,4096));data=np.ascontiguousarray(bsq.transpose(1,2,0));del bsq
 emit({'kind':'input','file':item['filename'],'shape':list(data.shape),'min':int(data.min()),'max':int(data.max()),'zero_samples':int(np.count_nonzero(data==0)),'saturated_samples':int(np.count_nonzero(data==65535)),'dn_sha256':hashlib.sha256(data.tobytes()).hexdigest(),'processing':'L1-calibrated; no filtering of values'})
 independent_prefix(data,item['filename'])
 for local in (3,0):run(data,item['filename'],local,9,index)
 if not index:
  # Train the preselected sensitivity table without adding another timing sweep.
  c=context(data,3,4);w=np.zeros((7,6),np.int32);out=np.empty(16,np.uint8);counts=np.zeros(4,np.uint64);start=time.perf_counter_ns();call(c,0,1,w,out,counts,lines=4096)
  priors[(3,4)]=np.clip((w.astype(np.int64)+128)>>8,-8192,8191).astype(np.int32);emit({'kind':'retrospective-training','file':item['filename'],'local':3,'nu_max':4,'seconds':(time.perf_counter_ns()-start)/1e9,'weights':priors[(3,4)].tolist(),'operational_table_availability_verified':False});lib.free_context(c)
 if index==1:independent_prefix(data,item['filename'],4);run(data,item['filename'],3,4,index,True)
 del data;gc.collect()
stream.close();print('LANDSAT_PILOT_COMPLETE',flush=True)
