from pathlib import Path
import os,sys,time,json,hashlib,ctypes as ct,gc,statistics,io,contextlib
import numpy as np,h5py
ROOT=Path(__file__).resolve().parent;DATA=Path(os.environ.get('CCSDS_DATA_DIR',str(ROOT.parent.parent/'data/hypso')))
os.sched_setaffinity(0,{int(os.environ.get('CCSDS_CPU','2'))})
P=ct.c_void_p;I=ct.c_int;U=ct.c_uint64
def setup(path):
    lib=ct.CDLL(str(path));lib.make_context.argtypes=[P,I,I,I,I,I,I];lib.make_context.restype=P
    lib.compute.argtypes=[P,I,I,I,P,P,P,P];lib.compute.restype=U;lib.free_context.argtypes=[P]
    return lib
lib=setup(ROOT/'build/libnativebip.so');checklib=setup(ROOT/'build/libcapture.so')
checklib.capture_compute.argtypes=[P,I,I,P,P,P,P];checklib.capture_compute.restype=U
old=json.loads((ROOT/'prior-followup-records.json').read_text());inputs=json.loads((ROOT/'selected-hypso-inputs.json').read_text())
ev=ROOT/'evidence';ev.mkdir(exist_ok=True);stream=(ev/'native-bip-comparison.jsonl').open('w',buffering=1)
def emit(q):stream.write(json.dumps(q)+'\n');print(json.dumps(q),flush=True)
def historical(name,local,nu):
    return next(r for r in old if r.get('kind')==('full-capture-adaptive' if nu==9 else 'nu4-full-sensitivity') and r.get('file')==name and r.get('local')==local)
def oracle_prefix(data,local,nu):
    sys.path.insert(0,os.environ.get('CCSDS_NTNU_DIR',str(ROOT.parent.parent/'external/ccsds123_issue_2_verification_model')))
    from ccsds123_i2_hlm import header as hd
    from ccsds123_i2_hlm.constants import ImageConstants
    from ccsds123_i2_hlm.predictor import Predictor
    from ccsds123_i2_hlm.sa_encoder import SampleAdaptiveEncoder
    h,w,z=data.shape;q=hd.Header(f'frame-u16be-{z}x{h}x{w}.raw')
    q.quantizer_fidelity_control_method=hd.QuantizerFidelityControlMethod.LOSSLESS
    q.sample_representative_flag=hd.SampleRepresentativeFlag.NOT_INCLUDED
    q.damping_table_array[:]=0;q.damping_offset_table_array[:]=0;q.fixed_damping_value=0;q.fixed_offset_value=0
    q.prediction_mode=hd.PredictionMode.FULL;q.local_sum_type=hd.LocalSumType.NARROW_COLUMN_ORIENTED if local==3 else hd.LocalSumType.WIDE_NEIGHBOR_ORIENTED
    q.set_weight_update_final_parameter(nu);q.sample_encoding_order=hd.SampleEncodingOrder.BI;q.sub_frame_interleaving_depth=z;q.entropy_coder_type=hd.EntropyCoderType.SAMPLE_ADAPTIVE
    q.set_unary_length_limit(32);q.set_initial_count_exponent(3);q.set_rescaling_counter_size(8);q.set_accumulator_init_constant(2);q.set_accumulator_init_table_to_default();q.check_legal_config()
    p=Predictor(q,ImageConstants(q),data.astype(np.int64));start=time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):p.run_predictor()
    e=SampleAdaptiveEncoder(q,ImageConstants(q),p.get_predictor_output())
    with contextlib.redirect_stdout(io.StringIO()):e.run_encoder()
    return e.bitstream.tobytes(),q.get_header_bitstreams()[0].tobytes(),time.perf_counter()-start
def run_prefix(data,name,local,nu):
    raw=np.ascontiguousarray(data);h,w,z=data.shape
    ctx=lib.make_context(raw.ctypes.data,w,h,z,local,nu,1);out=np.empty(data.size*6+16,dtype=np.uint8);counts=np.zeros(4,dtype=np.uint64);weights=np.zeros((z,6),dtype=np.int32)
    gold,head,seconds=oracle_prefix(data,local,nu)
    for g in (2,4,8):
        n=lib.compute(ctx,9,g,0,weights.ctypes.data,out.ctypes.data,counts.ctypes.data,0)
        assert out[:n].tobytes()==gold,(name,local,nu,g,'independent BIP mismatch')
    emit({'kind':'independent-native-BIP-prefix','file':name,'local':local,'nu_max':nu,'shape':list(data.shape),'body_bytes':len(gold),'body_sha256':hashlib.sha256(gold).hexdigest(),'header_hex':head.hex(),'groups_checked':[2,4,8],'all_equal':True,'reference_seconds':seconds})
    lib.free_context(ctx);gc.collect()
def run_full(data,name,local,nu,trace=False):
    raw=np.ascontiguousarray(data);h,w,z=data.shape;N=data.size;label={'file':name,'local':local,'nu_max':nu,'shape':list(data.shape)}
    out=np.empty(N*6+16,dtype=np.uint8);counts=np.zeros(4,dtype=np.uint64);w0=np.zeros((z,6),dtype=np.int32);wn=np.zeros_like(w0)
    ctx=checklib.make_context(raw.ctypes.data,w,h,z,local,nu,1);truth=np.empty(N,dtype=np.uint32);actual=np.empty_like(truth)
    n=checklib.capture_compute(ctx,0,1,w0.ctypes.data,out.ctypes.data,counts.ctypes.data,truth.ctypes.data)
    sha=hashlib.sha256(out[:n].tobytes()).hexdigest();hist=historical(name,local,nu)
    assert sha==hist.get('body_sha256',hist.get('sha256'))
    residualsha=hashlib.sha256(truth.tobytes()).hexdigest()
    for g in (4,8):
        nb=checklib.capture_compute(ctx,9,g,wn.ctypes.data,out.ctypes.data,counts.ctypes.data,actual.ctypes.data)
        assert nb==n
        if not np.array_equal(truth,actual):
            bad=np.flatnonzero(truth!=actual);np.savez_compressed(ev/f'failed-residuals-{name}-{local}-{nu}-{g}.npz',indices=bad,expected=truth[bad],actual=actual[bad]);raise AssertionError('full-cube residual mismatch')
        assert np.array_equal(wn,w0)
        emit(dict(label,kind='full-cube-residual-check',variant=9,group=g,samples=int(N),mismatches=0,final_weights_equal=True,body_bytes=int(nb),mapped_residual_sha256=residualsha,reference='specialized C scalar, whose BIL body matches historical reference hash; independent Python only prefixes'))
    checklib.free_context(ctx);del truth,actual;gc.collect()
    ctx=lib.make_context(raw.ctypes.data,w,h,z,local,nu,1)
    nb=lib.compute(ctx,9,8,0,wn.ctypes.data,out.ctypes.data,counts.ctypes.data,0);bip=out[:nb].tobytes();bipsha=hashlib.sha256(bip).hexdigest()
    variants=((2,1),(7,8),(9,4),(9,8));records=[]
    for trial in range(3):
        for v,g in variants[trial:]+variants[:trial]:
            start=time.perf_counter_ns();nb=lib.compute(ctx,v,g,0,wn.ctypes.data,out.ctypes.data,counts.ctypes.data,0);end=time.perf_counter_ns()
            digest=hashlib.sha256(out[:nb].tobytes()).hexdigest()
            assert nb==n and digest==(bipsha if v==9 else sha)
            rec=dict(label,kind='timing',trial=trial,variant=v,group=g,ns_sample=(end-start)/N,body_bytes=int(nb),output_order='BIP' if v==9 else 'BIL')
            records.append(rec);stream.write(json.dumps(rec)+'\n')
    med={f'{v}:{g}':statistics.median(r['ns_sample'] for r in records if (r['variant'],r['group'])==(v,g)) for v,g in variants}
    emit(dict(label,kind='summary',methods_ns=med,body_bytes=int(n),BIL_sha256=sha,BIP_sha256=bipsha,body_order_differs=bipsha!=sha,all_perband_residuals_equal=True,trials=3))
    if trace:
        arr=np.empty((512,8),dtype=np.uint64);nb=lib.compute(ctx,9,8,0,wn.ctypes.data,out.ctypes.data,counts.ctypes.data,arr.ctypes.data);arr=arr[:counts[3]]
        path=ev/f'trace-native-BIP-local{local}-nu{nu}-g8.npz';np.savez_compressed(path,trace=arr)
        emit(dict(label,kind='trace',path=path.name,rows=len(arr),array_sha256=hashlib.sha256(arr.tobytes()).hexdigest(),columns=['y','x','group_first_band','group_last_band_exclusive','group_begin_ns','group_finish_ns','complete_body_bytes','pending_bits'],first512_groups_only=True))
    lib.free_context(ctx);del out,bip;gc.collect()
name=inputs[1]['filename']
with h5py.File(DATA/'raw'/name,'r') as f:prefix=f['products/dn'][:8]
for local,nu in ((3,9),(0,9),(3,4)):run_prefix(prefix,name,local,nu)
del prefix;gc.collect()
for item in inputs:
    name=item['filename']
    with h5py.File(DATA/'raw'/name,'r') as f:data=f['products/dn'][:]
    for local in (3,0):run_full(data,name,local,9,trace=(name==inputs[1]['filename'] and local==3))
    del data;gc.collect()
name=inputs[1]['filename']
with h5py.File(DATA/'raw'/name,'r') as f:data=f['products/dn'][:]
run_full(data,name,3,4)
stream.close();print('NATIVE_BIP_COMPLETE',flush=True)
