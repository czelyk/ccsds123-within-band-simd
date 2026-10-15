
name=inputs[1]['filename']
with h5py.File(Path('work/ccsds_followup/raw')/name,'r') as f:data=f['products/dn'][:]
records,body,_=run_native(data,local=3,layout=0,variants=((0,1),(2,1),(3,2),(3,4),(3,8)),trials=3)
bil_full={'kind':'BIL-full-confirmation','file':name,'shape':list(data.shape),'local':3,'body_bytes':len(body),'body_sha256':hashlib.sha256(body).hexdigest(),'methods':summarize(records),'all_bodies_equal':True}
print(json.dumps(bil_full),flush=True)
prefix_data=np.ascontiguousarray(data[:128]);trace_results={}
for v,g in ((0,1),(2,1),(3,2),(3,4),(3,8)):
 rec,bb,tr=run_native(prefix_data,local=3,layout=0,variants=((v,g),),trials=1,trace_variant=(v,g))
 a=tr[(v,g)]['trace'];assert len(a)==128*120
 assert np.all(a[1:,6]>=a[:-1,6])
 first=[];last0=int(a[0,4])
 for Q in (256,1024,4096):
  j=int(np.searchsorted(a[:,6],Q));row=a[j]
  first.append({'body_quantum':Q,'row_index':j,'row_y':int(row[0]),'row_z':int(row[1]),'input_group_first':int(row[2]),'input_group_last':int(row[3]),'host_offset_us':(int(row[5])-last0)/1000,'within_group_finish_us':(int(row[5])-int(row[4]))/1000})
 trace_results[(v,g)]={'trace':a,'bytes':len(bb)}
 print(json.dumps({'kind':'BIL-output-trace','variant':v,'group':g,'bytes':len(bb),'trace_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'first_row_input_count':rec[0]['first_row_after_received'],'first_quantum_row_upper_bounds':first,'first_12_rows':[[int(x) for x in row[:4]]+[round((int(row[5])-int(row[4]))/1000,3),int(row[6]),int(row[7])] for row in a[:12]],'warning':'diagnostic host traces, row-end bounds, not arrival-scheduled or target timings'}),flush=True)
del data,body,prefix_data;gc.collect()
print('BIL_FULL_AND_TRACES_COMPLETE',flush=True)

