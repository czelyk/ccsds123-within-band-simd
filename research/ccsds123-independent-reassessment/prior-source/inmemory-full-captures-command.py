
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
full_results={}
for item in inputs:
 name=item['filename']
 with h5py.File(Path('work/ccsds_followup/raw')/name,'r') as f:data=f['products/dn'][:]
 for local in (3,0):
  records,body,traces=run_native(data,local=local,layout=1,trials=3)
  head=make_header(data.shape,local).get_header_bitstreams()[0].tobytes()
  result={'kind':'full-capture-adaptive','file':name,'shape':list(data.shape),'layout':'BIP','local':local,'samples':int(data.size),'body_bytes':len(body),'header_bytes':len(head),'body_sha256':hashlib.sha256(body).hexdigest(),'methods':summarize(records),'all_bodies_equal':True,'full_reference':'specialized scalar; independent NTNU validation on full-width first8 rows'}
  full_results[(name,local,'BIP')]=(result,records)
  print(json.dumps(result),flush=True)
 del data,body;gc.collect()
print('FULL_BIP_COMPLETE',flush=True)

