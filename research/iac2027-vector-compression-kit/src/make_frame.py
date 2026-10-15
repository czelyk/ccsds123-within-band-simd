import sys,pathlib,contextlib,io,struct,json,os
import numpy as np
from scipy.io import loadmat
HERE=pathlib.Path(__file__).resolve().parent
REFERENCE=pathlib.Path(os.environ.get('CCSDS_REFERENCE_ROOT',str(HERE.parent/('reference' if (HERE.parent/'reference').exists() else 'ntnu'))))
DATA=pathlib.Path(os.environ.get('CCSDS_DATA_ROOT',str(HERE.parent/('data' if (HERE.parent/'data').exists() else '.'))))
sys.path.insert(0,str(REFERENCE))
from ccsds123_i2_hlm import header as hd
from ccsds123_i2_hlm.constants import ImageConstants
from ccsds123_i2_hlm.predictor import Predictor
from ccsds123_i2_hlm.sa_encoder import SampleAdaptiveEncoder

def generate(data,label,nu_max,training=None,bil=False):
  height,width,bands=data.shape
  for local_sum in (hd.LocalSumType.NARROW_COLUMN_ORIENTED,hd.LocalSumType.WIDE_NEIGHBOR_ORIENTED):
    h=hd.Header(f'frame-u16be-{bands}x{height}x{width}.raw')
    h.quantizer_fidelity_control_method=hd.QuantizerFidelityControlMethod.LOSSLESS
    h.sample_representative_flag=hd.SampleRepresentativeFlag.NOT_INCLUDED
    h.damping_table_array[:]=0;h.damping_offset_table_array[:]=0;h.fixed_damping_value=0;h.fixed_offset_value=0
    h.prediction_mode=hd.PredictionMode.FULL
    h.local_sum_type=local_sum
    h.set_weight_update_final_parameter(nu_max)
    h.sample_encoding_order=hd.SampleEncodingOrder.BI if bil else hd.SampleEncodingOrder.BSQ
    h.sub_frame_interleaving_depth=1 if bil else 0
    h.entropy_coder_type=hd.EntropyCoderType.SAMPLE_ADAPTIVE
    h.set_unary_length_limit(32);h.set_initial_count_exponent(3);h.set_rescaling_counter_size(8)
    h.set_accumulator_init_constant(2);h.set_accumulator_init_table_to_default()
    weights=None
    if training is not None:
      # A held-out spatial crop of the same acquisition is a limited exogenous
      # calibration experiment, not a reproduction of the authors' corpus.
      train=Predictor(h,ImageConstants(h),training)
      with contextlib.redirect_stdout(io.StringIO()):train.run_predictor()
      weights=np.clip(np.rint(train.weight_vector[-1,-1]/256),-8192,8191).astype(np.int64)
      h.set_weight_component_resolution(11)
      h.set_weight_update_initial_parameter(9);h.set_weight_update_final_parameter(9)
      h.weight_exponent_offset_flag=hd.WeightExponentOffsetFlag.NOT_ALL_ZERO
      h.weight_exponent_offset_value=5;h.set_weight_exponent_offset_table_array_to_default()
      h.weight_exponent_offset_table_flag=hd.WeightExponentOffsetTableFlag.INCLUDED
      h.weight_init_method=hd.WeightInitMethod.CUSTOM;h.weight_init_resolution=14
      h.weight_init_table_flag=hd.WeightInitTableFlag.INCLUDED;h.weight_init_table=weights
    h.check_legal_config()
    constants=ImageConstants(h);p=Predictor(h,constants,data)
    with contextlib.redirect_stdout(io.StringIO()):p.run_predictor()
    e=SampleAdaptiveEncoder(h,constants,p.get_predictor_output())
    with contextlib.redirect_stdout(io.StringIO()):e.run_encoder()
    golden=e.bitstream.tobytes()
    header=h.get_header_bitstreams()[0].tobytes()
    dest=HERE/f'frame_{label}_nu{nu_max}_{local_sum.name}.bin'
    with dest.open('wb') as f:
        f.write(struct.pack('<6I',width,height,bands,local_sum.value|(nu_max<<8)|(int(training is not None)<<16)|(int(bil)<<17),len(golden),len(header)))
        np.asarray(data.transpose(2,0,1),dtype='<u2').tofile(f)
        f.write(golden);f.write(header)
        if weights is not None:np.asarray(weights,dtype='<i4').tofile(f)
    print(json.dumps({'file':dest.name,'body_bytes':len(golden),'body_bits':len(e.bitstream),'header_hex':header.hex()}),flush=True)

if __name__=='__main__':
  for label,file,key in [('pines','Indian_pines_corrected.mat','indian_pines_corrected'),('pavia','PaviaU.mat','paviaU'),('salinas','Salinas_corrected.mat','salinas_corrected')]:
    d=loadmat(DATA/file)[key][:64,:128,:6].astype(np.int64)
    if label=='salinas':d=d+11 # Explicit shift for this signed, corrected dataset.
    for nu in [4,9]:generate(d,label,nu)
    whole=loadmat(DATA/file)[key].astype(np.int64)
    if label=='salinas':whole=whole+11
    generate(d,label+'_fixed',9,training=whole[64:128,:128,:6])
    generate(d,label+'_bil',9,bil=True)
    generate(d,label+'_bil_fixed',9,training=whole[64:128,:128,:6],bil=True)
  rng=np.random.default_rng(20261015)
  for label,d in [('noise',rng.integers(0,65536,(24,64,6),dtype=np.int64)),('constant',np.full((24,64,6),32768,dtype=np.int64)),('checkerboard',np.repeat((np.indices((24,64)).sum(axis=0)%2*65535)[:,:,None],6,axis=2))]:generate(d,label,9)
