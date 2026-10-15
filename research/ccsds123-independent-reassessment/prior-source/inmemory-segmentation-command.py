
segmented_results={}
for item in inputs[1:]:
 name=item['filename']
 with h5py.File(Path('work/ccsds_followup/raw')/name,'r') as f:data=f['products/dn'][:]
 K=32;prefix=np.ascontiguousarray(data[:K]);suffix=np.ascontiguousarray(data[K:]);z=data.shape[2];w=data.shape[1]
 for local in (3,0):
  cp=create(prefix.ctypes.data,w,K,z,local,9,1);cs=create(suffix.ctypes.data,w,len(suffix),z,local,9,1)
  op=np.empty(prefix.size*6+16,dtype=np.uint8);osuf=np.empty(suffix.size*6+16,dtype=np.uint8);counts=np.zeros(4,dtype=np.uint64);wt=np.zeros((z,6),dtype=np.int32);blank=np.zeros_like(wt)
  npfx=compute(cp,0,1,0,wt.ctypes.data,op.ctypes.data,counts.ctypes.data,0);bp=op[:npfx].tobytes();tab0=quantize(wt)
  nf=compute(cs,4,1,0,tab0.ctypes.data,osuf.ctypes.data,counts.ctypes.data,0);bf=osuf[:nf].tobytes()
  na=compute(cs,0,1,0,blank.ctypes.data,osuf.ctypes.data,counts.ctypes.data,0);ba=osuf[:na].tobytes()
  hf=make_header(prefix.shape,local).get_header_bitstreams()[0].tobytes()+make_header(suffix.shape,local,tab0).get_header_bitstreams()[0].tobytes()
  ha=make_header(prefix.shape,local).get_header_bitstreams()[0].tobytes()+make_header(suffix.shape,local).get_header_bitstreams()[0].tobytes()
  records=[]
  for trial in range(3):
   for v in ((4,0) if trial%2==0 else (0,4)):
    start=time.perf_counter_ns()
    np1=compute(cp,0,1,0,wt.ctypes.data,op.ctypes.data,counts.ctypes.data,0)
    if v==4:tab=quantize(wt);assert np.array_equal(tab,tab0)
    else:tab=blank
    ns1=compute(cs,v,1,0,tab.ctypes.data,osuf.ctypes.data,counts.ctypes.data,0)
    end=time.perf_counter_ns()
    assert op[:np1].tobytes()==bp
    assert osuf[:ns1].tobytes()==(bf if v==4 else ba)
    records.append({'trial':trial,'suffix_variant':v,'total_ns_sample':(end-start)/data.size})
  adap=full_results[(name,local,'BIP')][0]['body_bytes']+19
  result={'kind':'two-image-prefix32','file':name,'local':local,'prefix_lines':K,'fixed_suffix_total_bytes':len(bp)+len(bf)+len(hf),'adaptive_split_total_bytes':len(bp)+len(ba)+len(ha),'fixed_delta_percent':100*((len(bp)+len(bf)+len(hf))/adap-1),'adaptive_split_delta_percent':100*((len(bp)+len(ba)+len(ha))/adap-1),'methods':{str(v):statistics.median(r['total_ns_sample'] for r in records if r['suffix_variant']==v) for v in (4,0)},'trials':records,'prefix_sha256':hashlib.sha256(bp).hexdigest(),'fixed_suffix_sha256':hashlib.sha256(bf).hexdigest(),'adaptive_suffix_sha256':hashlib.sha256(ba).hexdigest(),'all_bodies_equal':True,'framing':'two independent CCSDS images; not same adaptive full-image bitstream or claim of exact reproduction of Barrios2024'}
  segmented_results[(name,local)]=result;print(json.dumps(result),flush=True)
  destroy(cp);destroy(cs)
 del data,prefix,suffix,op,osuf,bp,bf,ba;gc.collect()
print('SEGMENTED_COMPLETE',flush=True)

