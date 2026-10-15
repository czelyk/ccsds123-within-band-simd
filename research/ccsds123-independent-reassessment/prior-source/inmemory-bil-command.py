
print(json.dumps({'kind':'fixed-summary','count':len(fixed_results),'rows':[{'scene':k[0].split('_2022')[0],'local':k[1],'cal':k[2],'delta_percent':r['size_change_percent'],'vector_ns':r['methods']['4']['total_ns_sample'],'scalar_ns':r['methods']['6']['total_ns_sample']} for k,r in fixed_results.items()]}),flush=True)
bil_results={}
for item in inputs:
 name=item['filename']
 with h5py.File(Path('work/ccsds_followup/raw')/name,'r') as f:data=f['products/dn'][:128]
 for local in (3,0):
  records,body,traces=run_native(data,local=local,layout=0,trials=3)
  result={'kind':'BIL-replay','file':name,'shape':list(data.shape),'local':local,'body_bytes':len(body),'body_sha256':hashlib.sha256(body).hexdigest(),'methods':summarize(records),'all_bodies_equal':True}
  bil_results[(name,local)]=(result,records);print(json.dumps(result),flush=True)
 del data,body;gc.collect()
print('BIL_REPLAY_COMPLETE',flush=True)

