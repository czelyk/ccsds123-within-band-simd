from pathlib import Path
import os,time,json,hashlib,ctypes as ct,statistics,gc,platform
import numpy as np,h5py
ROOT=Path(__file__).resolve().parent
DATA=Path(os.environ.get('CCSDS_DATA_DIR',str(ROOT.parent.parent/'data/hypso')))
os.sched_setaffinity(0,{int(os.environ.get('CCSDS_CPU','2'))})
lib=ct.CDLL(str(ROOT/'build/libreassessment.so'))
P=ct.c_void_p;I=ct.c_int;U=ct.c_uint64
lib.make_context.argtypes=[P,I,I,I,I,I,I];lib.make_context.restype=P
lib.compute.argtypes=[P,I,I,I,P,P,P,P];lib.compute.restype=U
lib.free_context.argtypes=[P]
old=json.loads((ROOT/'prior-followup-records.json').read_text())
inputs=json.loads((ROOT/'selected-hypso-inputs.json').read_text())
evidence=ROOT/'evidence';evidence.mkdir(exist_ok=True)
stream=(evidence/'tap-comparison.jsonl').open('w',buffering=1)
def emit(q):
    stream.write(json.dumps(q)+'\n');print(json.dumps(q),flush=True)
def expected(name,local,nu,prefix):
    if nu==4:
        r=next(r for r in old if r.get('kind')==('nu4-independent-prefix' if prefix else 'nu4-full-sensitivity'))
        return r['sha256']
    kind='independent-full-band-prefix' if prefix else 'full-capture-adaptive'
    r=next(r for r in old if r.get('kind')==kind and r.get('file')==name and r.get('local')==local)
    return r['adaptive_sha256'] if prefix else r['body_sha256']
def run(data,name,local,nu,layout,variants,trials,reference_prefix=False,trace=False):
    h,w,z=data.shape;raw=np.ascontiguousarray(data if layout else data.transpose(0,2,1))
    ctx=lib.make_context(raw.ctypes.data,w,h,z,local,nu,layout);assert ctx
    out=np.empty(data.size*6+16,dtype=np.uint8);counts=np.zeros(4,dtype=np.uint64);weights=np.zeros((z,6),dtype=np.int32)
    n=lib.compute(ctx,0,1,0,weights.ctypes.data,out.ctypes.data,counts.ctypes.data,0)
    body=out[:n].tobytes();sha=hashlib.sha256(body).hexdigest()
    assert sha==expected(name,local,nu,reference_prefix),(name,local,nu,'historical reference mismatch')
    label={'file':name,'local':local,'nu_max':nu,'layout':'BIP' if layout else 'BIL','shape':list(data.shape)}
    for v,g in variants:
        nn=lib.compute(ctx,v,g,0,weights.ctypes.data,out.ctypes.data,counts.ctypes.data,0)
        assert nn==n and out[:nn].tobytes()==body,(label,v,g,'warmup mismatch')
    records=[]
    for trial in range(trials):
        order=variants[trial%len(variants):]+variants[:trial%len(variants)]
        for v,g in order:
            start=time.perf_counter_ns();nn=lib.compute(ctx,v,g,0,weights.ctypes.data,out.ctypes.data,counts.ctypes.data,0);end=time.perf_counter_ns()
            assert nn==n and out[:nn].tobytes()==body,(label,v,g,'timed mismatch')
            r=dict(label,kind='timing',trial=trial,variant=v,group=g,ns_sample=(end-start)/data.size,body_bytes=int(n),accepted=int(counts[0]),rejected=int(counts[1]),first_input_rows=int(counts[2]))
            records.append(r);stream.write(json.dumps(r)+'\n')
    med={f'{v}:{g}':statistics.median(r['ns_sample'] for r in records if (r['variant'],r['group'])==(v,g)) for v,g in variants}
    emit(dict(label,kind='reference' if reference_prefix else 'summary',methods_ns=med,body_bytes=int(n),body_sha256=sha,all_equal=True,trials=trials))
    if trace:
        for v,g in variants:
            arr=np.empty((h*z,8),dtype=np.uint64)
            nn=lib.compute(ctx,v,g,0,weights.ctypes.data,out.ctypes.data,counts.ctypes.data,arr.ctypes.data)
            assert nn==n and out[:nn].tobytes()==body
            arr=arr[:counts[3]]
            path=evidence/f'trace-finnmark-local{local}-nu{nu}-v{v}-g{g}.npz'
            np.savez_compressed(path,trace=arr)
            emit(dict(label,kind='trace',variant=v,group=g,path=path.name,rows=len(arr),array_sha256=hashlib.sha256(arr.tobytes()).hexdigest(),columns=['y','z','group_first','group_last_exclusive','group_begin_ns','row_finish_ns','complete_body_bytes','pending_bits']))
    lib.free_context(ctx)
    return records
emit({'kind':'environment','compiler':'clang18 O3 march=native shared library','cpu':platform.processor(),'affinity':sorted(os.sched_getaffinity(0)),'frequency_controlled':False,'timing_exclusions':['input file I/O','context allocation','output comparisons','headers','output file or telemetry transfer','DMA and system interference']})
for item in inputs:
    name=item['filename'];path=DATA/'raw'/name
    with h5py.File(path,'r') as f:data=f['products/dn'][:]
    emit({'kind':'input','file':name,'shape':list(data.shape),'dn_sha256':hashlib.sha256(data.tobytes()).hexdigest()})
    for local in (3,0):
        run(data[:8],name,local,9,1,((0,1),(2,1),(7,4),(7,8),(8,1)),1,True)
        run(data,name,local,9,1,((0,1),(2,1),(7,4),(7,8),(8,1)),3)
    del data;gc.collect()
name=inputs[1]['filename']
with h5py.File(DATA/'raw'/name,'r') as f:data=f['products/dn'][:]
run(data[:8],name,3,4,1,((0,1),(2,1),(7,4),(7,8),(8,1)),1,True)
run(data,name,3,4,1,((0,1),(2,1),(7,4),(7,8),(8,1)),3)
run(data,name,3,9,0,((0,1),(2,1),(7,2),(7,4),(7,8),(8,1)),5,trace=True)
stream.close()
print('NEW_COMPARATOR_COMPLETE',flush=True)
