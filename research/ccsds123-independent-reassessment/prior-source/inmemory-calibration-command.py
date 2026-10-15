
# Expose the state already calculated during normal prefix compression.
csrc2=csrc.replace('f->endweights=learn_lines?weights:0;','f->endweights=(learn_lines||variant==0)?weights:0;')
assert csrc2!=csrc
mainmod2=compile_ir(csrc2,'bench_with_state_export')
for typ in ('scalar','avx','frozen'):
 for k in range(3,7):assert api('LLVMLinkModules2',I,[P,P])(mainmod2,compile_ir((SRC/f'{typ}{k}.c').read_text(),f'{typ}{k}_v2'))==0
ee2=P();err=S();assert api('LLVMCreateExecutionEngineForModule',I,[ct.POINTER(P),P,ct.POINTER(S)])(ct.byref(ee2),mainmod2,ct.byref(err))==0,err.value
create=ct.CFUNCTYPE(P,P,I,I,I,I,I,I)(get(ee2,b'make_context'))
compute=ct.CFUNCTYPE(U,P,I,I,I,P,P,P,P)(get(ee2,b'compute'))
destroy=ct.CFUNCTYPE(None,P)(get(ee2,b'free_context'))
print(json.dumps({'kind':'source-v2','sha256':hashlib.sha256(csrc2.encode()).hexdigest(),'only_change':'export already computed final weights on scalar compression; original predictor kernels unchanged'}),flush=True)
def quantize(w):return np.clip((w.astype(np.int64)+128)>>8,-8192,8191).astype(np.int32)
def defaults(z):
 tab=np.zeros((z,6),dtype=np.int32)
 for band in range(z):
  if band:tab[band,3]=1792
  if band>1:tab[band,4]=224
  if band>2:tab[band,5]=28
 return tab
def learn(data,lines,local=3,layout=1):
 h,w,z=data.shape;raw=np.ascontiguousarray(data if layout else data.transpose(0,2,1));context=create(raw.ctypes.data,w,h,z,local,9,layout);assert context
 weights=np.zeros((z,6),dtype=np.int32);counts=np.zeros(4,dtype=np.uint64);out=np.zeros(16,dtype=np.uint8)
 t=time.perf_counter_ns();compute(context,0,1,lines,weights.ctypes.data,out.ctypes.data,counts.ctypes.data,0);ns=time.perf_counter_ns()-t;destroy(context)
 return weights,quantize(weights),ns
fixed_results={};prior_tables={}
for index,item in enumerate(inputs):
 name=item['filename']
 with h5py.File(Path('work/ccsds_followup/raw')/name,'r') as f:
  data=f['products/dn'][:];down=str(f.attrs['timestamp_downlinked']);acq=str(f.attrs['timestamp_acquired'])
 for local in (3,0):
  if index==0:
   ww,table,lns=learn(data,data.shape[0],local)
   prior_tables[local]=table.copy()
   print(json.dumps({'kind':'ground-calibration-source','file':name,'local':local,'acquired':acq,'downlinked':down,'weights_sha256':hashlib.sha256(table.tobytes()).hexdigest(),'host_learning_seconds':lns/1e9,'per-test_training_cost':'none: explicitly a previously ground-derived stored table'}),flush=True)
  h,w,z=data.shape;raw=np.ascontiguousarray(data);context=create(raw.ctypes.data,w,h,z,local,9,1);assert context
  out=np.empty(data.size*6+16,dtype=np.uint8);counts=np.zeros(4,dtype=np.uint64);w19=np.zeros((z,6),dtype=np.int32)
  choices=[('default',0,defaults(z))]
  if index:choices.append(('prior-first-capture',0,prior_tables[local]))
  for K in (8,32,100):
   compute(context,0,1,K,w19.ctypes.data,out.ctypes.data,counts.ctypes.data,0);choices.append((f'prefix{K}-reencode',K,quantize(w19)))
  for label,K,initial in choices:
   tab=initial.copy()
   n=compute(context,6,1,0,tab.ctypes.data,out.ctypes.data,counts.ctypes.data,0);base=out[:n].tobytes();digest=hashlib.sha256(base).hexdigest()
   head=make_header(data.shape,local,tab).get_header_bitstreams()[0].tobytes()
   records=[]
   for trial in range(3):
    for v in ((4,6) if trial%2==0 else (6,4)):
     start=time.perf_counter_ns();training_ns=0
     if K:
      ts=time.perf_counter_ns();compute(context,0,1,K,w19.ctypes.data,out.ctypes.data,counts.ctypes.data,0);tab=quantize(w19);training_ns=time.perf_counter_ns()-ts
      assert np.array_equal(tab,initial)
     ts=time.perf_counter_ns();n=compute(context,v,1,0,tab.ctypes.data,out.ctypes.data,counts.ctypes.data,0);end=time.perf_counter_ns()
     assert out[:n].tobytes()==base,(name,local,label,v,'fixed output mismatch')
     records.append({'trial':trial,'variant':v,'total_ns_sample':(end-start)/data.size,'encode_ns_sample':(end-ts)/data.size,'training_seconds':training_ns/1e9})
   base_adapt=full_results[(name,local,'BIP')][0];total=len(base)+len(head);adap=base_adapt['body_bytes']+base_adapt['header_bytes']
   med={str(v):{'total_ns_sample':statistics.median(r['total_ns_sample'] for r in records if r['variant']==v),'encode_ns_sample':statistics.median(r['encode_ns_sample'] for r in records if r['variant']==v),'training_seconds':statistics.median(r['training_seconds'] for r in records if r['variant']==v)} for v in (4,6)}
   result={'kind':'full-capture-fixed','file':name,'local':local,'calibration':label,'causal':True,'training_lines':K,'body_bytes':len(base),'header_bytes':len(head),'total_bytes':total,'size_change_percent':100*(total/adap-1),'sha256':digest,'weights_sha256':hashlib.sha256(tab.tobytes()).hexdigest(),'methods':med,'trials':records,'all_bodies_equal':True}
   fixed_results[(name,local,label)]=result;print(json.dumps(result),flush=True)
  destroy(context)
 del data,raw,out,base;gc.collect()
print('FIXED_FULL_CAPTURE_COMPLETE',flush=True)

