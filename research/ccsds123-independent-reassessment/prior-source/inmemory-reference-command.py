
sys.path.insert(0,str(Path('work/cycle13/ntnu').resolve()))
from ccsds123_i2_hlm import header as hd
from ccsds123_i2_hlm.constants import ImageConstants
from ccsds123_i2_hlm.predictor import Predictor
from ccsds123_i2_hlm.sa_encoder import SampleAdaptiveEncoder
import contextlib,io
def make_header(shape,local,weights=None):
 h,w,z=shape
 q=hd.Header(f'frame-u16be-{z}x{h}x{w}.raw')
 q.quantizer_fidelity_control_method=hd.QuantizerFidelityControlMethod.LOSSLESS
 q.sample_representative_flag=hd.SampleRepresentativeFlag.NOT_INCLUDED
 q.damping_table_array[:]=0;q.damping_offset_table_array[:]=0;q.fixed_damping_value=0;q.fixed_offset_value=0
 q.prediction_mode=hd.PredictionMode.FULL;q.local_sum_type=hd.LocalSumType.NARROW_COLUMN_ORIENTED if local==3 else hd.LocalSumType.WIDE_NEIGHBOR_ORIENTED
 q.set_weight_update_final_parameter(9);q.sample_encoding_order=hd.SampleEncodingOrder.BI;q.sub_frame_interleaving_depth=1;q.entropy_coder_type=hd.EntropyCoderType.SAMPLE_ADAPTIVE
 q.set_unary_length_limit(32);q.set_initial_count_exponent(3);q.set_rescaling_counter_size(8);q.set_accumulator_init_constant(2);q.set_accumulator_init_table_to_default()
 if weights is not None:
  q.set_weight_component_resolution(11);q.set_weight_update_initial_parameter(9);q.set_weight_update_final_parameter(9)
  q.weight_exponent_offset_flag=hd.WeightExponentOffsetFlag.NOT_ALL_ZERO;q.weight_exponent_offset_value=5;q.set_weight_exponent_offset_table_array_to_default();q.weight_exponent_offset_table_flag=hd.WeightExponentOffsetTableFlag.INCLUDED
  q.weight_init_method=hd.WeightInitMethod.CUSTOM;q.weight_init_resolution=14;q.weight_init_table_flag=hd.WeightInitTableFlag.INCLUDED;q.weight_init_table=weights.astype(np.int64)
 q.check_legal_config()
 return q
def independent(data,local=3,weights=None):
 h=make_header(data.shape,local,weights);p=Predictor(h,ImageConstants(h),data.astype(np.int64));t=time.perf_counter()
 with contextlib.redirect_stdout(io.StringIO()):p.run_predictor()
 e=SampleAdaptiveEncoder(h,ImageConstants(h),p.get_predictor_output())
 with contextlib.redirect_stdout(io.StringIO()):e.run_encoder()
 body=e.bitstream.tobytes();heads=h.get_header_bitstreams()[0].tobytes()
 return body,heads,p,time.perf_counter()-t
inputs=json.loads(Path('work/ccsds_followup/selected_hypso_inputs.json').read_text())
results=[];reference_checks=[];prior_tables={}
for item in inputs:
 name=item['filename'];path=Path('work/ccsds_followup/raw')/name
 with h5py.File(path,'r') as f:data=f['products/dn'][:8,:,:]
 for local in (3,0):
  gold,head,p,secs=independent(data,local)
  records,body,_=run_native(data,local=local,trials=1)
  assert body==gold,(name,local,'full-band reference mismatch')
  # Explicitly validate causal learning's post-last-sample state.
  learned,fixed,ns=learn(data,8,local)
  expected=p.weight_vector[-1,-1].copy();u=p.local_difference_vector[-1,-1];err=p.double_resolution_prediction_error[-1,-1]
  rho=p.weight_update_scaling_exponent[-1]
  for z in range(data.shape[2]):
   for i in range(6):
    delta=int(np.floor((1 if err[z]>=0 else -1)*int(u[z,i])*2.0**(-int(rho))))
    expected[z,i]=min(2097151,max(-2097152,int(expected[z,i])+(delta+1)//2))
  assert np.array_equal(learned,expected),(name,local,'learning state mismatch')
  fg,fh,pp,fs=independent(data,local,fixed)
  fr,fb,_=run_native(data,local=local,weights=fixed,variants=((6,1),(4,1)),trials=1)
  assert fg==fb,(name,local,'fixed reference mismatch')
  rec={'kind':'independent-full-band-prefix','file':name,'shape':list(data.shape),'local':local,'adaptive_body_bytes':len(gold),'adaptive_sha256':hashlib.sha256(gold).hexdigest(),'fixed_body_bytes':len(fg),'fixed_sha256':hashlib.sha256(fg).hexdigest(),'predictor_learning_state_match':True,'all_methods_groups_match':True,'reference_seconds':secs+fs}
  reference_checks.append(rec);print(json.dumps(rec),flush=True)
  del p,pp;gc.collect()
print('REFERENCE_PREFIXES_COMPLETE',flush=True)

