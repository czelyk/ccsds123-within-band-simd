
import types
create_regular=create
def create_nu4(rawptr,w,h,z,local,nu,layout):return create_regular(rawptr,w,h,z,local,4,layout)
run_nu4=types.FunctionType(run_native.__code__,dict(run_native.__globals__,create=create_nu4),'run_nu4',run_native.__defaults__)
header_regular=make_header
def make_header_nu4(shape,local,weights=None):
 q=header_regular(shape,local,weights)
 if weights is None:q.set_weight_update_final_parameter(4)
 q.check_legal_config();return q
independent_nu4=types.FunctionType(independent.__code__,dict(independent.__globals__,make_header=make_header_nu4),'independent_nu4',independent.__defaults__)
name=inputs[1]['filename']
with h5py.File(Path('work/ccsds_followup/raw')/name,'r') as f:data=f['products/dn'][:];dimensions={k:{'shape':list(f[k].shape),'dimensions':[str(d.label) for d in f[k].dims]} for k in ('products/dn',)}
gold,head,p,secs=independent_nu4(data[:8],3)
rr,bb,_=run_nu4(data[:8],local=3,layout=1,trials=1)
assert bb==gold
print(json.dumps({'kind':'nu4-independent-prefix','file':name,'local':3,'shape':list(data[:8].shape),'body_bytes':len(gold),'sha256':hashlib.sha256(gold).hexdigest(),'all_groups_match':True,'reference_seconds':secs,'dimensions':dimensions}),flush=True)
del p;gc.collect()
rr,bb,_=run_nu4(data,local=3,layout=1,trials=3)
nu4_result={'kind':'nu4-full-sensitivity','file':name,'local':3,'layout':'BIP','shape':list(data.shape),'body_bytes':len(bb),'header_bytes':len(head),'sha256':hashlib.sha256(bb).hexdigest(),'methods':summarize(rr),'all_bodies_equal':True,'fixed_prior9_size_delta_percent':100*(fixed_results[(name,3,'prior-first-capture')]['total_bytes']/(len(bb)+len(head))-1)}
print(json.dumps(nu4_result),flush=True)
del data,bb,gold;gc.collect()
print('NU4_SENSITIVITY_COMPLETE',flush=True)

