
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
compact_results={}
for item in inputs:
 name=item['filename']
 with h5py.File(Path('work/ccsds_followup/raw')/name,'r') as f:data=f['products/dn'][:]
 for local in (3,0):
  # Byte comparisons to the already independently checked scalar path.
  r,b,_=run_native(data[:8],local=local,layout=1,variants=((7,1),(7,2),(7,4),(7,8)),trials=1)
  r,b,_=run_native(data,local=local,layout=1,variants=((7,2),(7,4),(7,8)),trials=3)
  q={'kind':'compact-band-BIP','file':name,'local':local,'body_bytes':len(b),'body_sha256':hashlib.sha256(b).hexdigest(),'methods':summarize(r),'all_bodies_equal':True,'first8_allgroups_equal':True}
  compact_results[(name,local,'BIP')]=q;print(json.dumps(q),flush=True)
 del data,b;gc.collect()
name=inputs[1]['filename']
with h5py.File(Path('work/ccsds_followup/raw')/name,'r') as f:data=f['products/dn'][:]
r,b,_=run_native(data,local=3,layout=0,variants=((7,2),(7,4),(7,8)),trials=3,trace_variant=(7,8))
q={'kind':'compact-band-BIL','file':name,'local':3,'body_bytes':len(b),'body_sha256':hashlib.sha256(b).hexdigest(),'methods':summarize(r),'all_bodies_equal':True}
compact_results[(name,3,'BIL')]=q;print(json.dumps(q),flush=True)
a=_[(7,8)]['trace'];trace_results[(7,8)]={'trace':a,'bytes':len(b)}
print(json.dumps({'kind':'compact-band-trace','group':8,'first_input_rows':r[0]['first_row_after_received'],'first1024_body_row':int(np.searchsorted(a[:,6],1024)),'trace_sha256':hashlib.sha256(a.tobytes()).hexdigest()}),flush=True)
del data,b;gc.collect()
print('COMPACT_BASELINE_COMPLETE',flush=True)

