
N=956*684*120;W=684;Z=120;H=956
main_rows=[]
for name in [x['filename'] for x in inputs]:
 for local in (3,0):
  q=full_results[(name,local,'BIP')][0];m=q['methods'];best=min(m[f'{v}:1']['median_ns'] for v in (0,1,5))
  main_rows.append({'scene':name.split('_2022')[0],'local':local,'best_scalar_ns':best,'proposed_ns':m['2:1']['median_ns'],'band4_ns':m['3:4']['median_ns'],'band8_ns':m['3:8']['median_ns'],'proposed_speedup_scalar':best/m['2:1']['median_ns'],'band8_speedup_proposed':m['2:1']['median_ns']/m['3:8']['median_ns'],'adaptive_total_bytes':q['body_bytes']+19,'compression_ratio':2*N/(q['body_bytes']+19)})
print(json.dumps({'kind':'all-main-cases-summary','rows':main_rows}),flush=True)
q=full_results[(inputs[1]['filename'],3,'BIP')][0]
bip_account=[]
for label,ns,bytes_out in [('scalar',q['methods']['0:1']['median_ns'],q['body_bytes']+19),('proposed',q['methods']['2:1']['median_ns'],q['body_bytes']+19),('band4',q['methods']['3:4']['median_ns'],q['body_bytes']+19),('band8',q['methods']['3:8']['median_ns'],q['body_bytes']+19),('fixed-prior9',fixed_results[(inputs[1]['filename'],3,'prior-first-capture')]['methods']['4']['total_ns_sample'],fixed_results[(inputs[1]['filename'],3,'prior-first-capture')]['total_bytes'])]:
 c=N*ns/1e9;line=W*Z*ns/1e9;capture=H/22;finish=1/22+line+(H-1)*max(1/22,line)
 bip_account.append({'method':label,'host_capacity_Msamples_s':1000/ns,'host_encoding_seconds':c,'capture22Hz_seconds':capture,'buffered_capture_then_host_encoding_seconds':capture+c,'ideal_line_overlap_finish_seconds':finish,'output_bytes':bytes_out,'compression_ratio':2*N/bytes_out})
R=106e6;a=W/R;bil_account=[]
for label,key,g in [('scalar','0:1',1),('proposed','2:1',1),('band2','3:2',2),('band4','3:4',4),('band8','3:8',8)]:
 ns=bil_full['methods'][key]['median_ns'];c=W*g*ns/1e9;K=H*Z//g;F=g*a+c+(K-1)*max(g*a,c)
 v=0 if label=='scalar' else 2 if label=='proposed' else 3;t=trace_results[(v,g)]['trace'];j=int(np.searchsorted(t[:,6],1024));row=t[j];first=g*a+(int(row[5])-int(row[4]))/1e9
 bil_account.append({'method':label,'host_ns_sample':ns,'host_capacity_Msamples_s':1000/ns,'group_rows':g,'input_wait_us':g*a*1e6,'host_trace_first1024_body_bytes_row_end_upper_us_with_arrival':first*1e6,'constant_service_cube_finish_seconds':F,'surrogate_capture_seconds':N/R,'sustainable_on_measured_host_at106M':ns<=1e9/R})
accounting={'kind':'analytical-accounting','BIP_nominal_HYPSO_class':bip_account,'BIL_HYPSO_data_CHIME2020_rate_surrogate':bil_account,'BIL_formula':'F=g*a+c+(K-1)*max(g*a,c), a=W/R, c=g*W*host_ns_per_sample; uniform service approximation, not WCET or Renode','memory_bytes':{'common_two_line_ring':4*W*Z,'proposed_scratch':40*W,'current_band_scratch_max8':256*W,'optimized_band2_scratch_estimate':64*W,'optimized_band4_scratch_estimate':128*W,'proposed_ring_plus_scratch':4*W*Z+40*W,'current_band_ring_plus_scratch':4*W*Z+256*W,'prefix8_input_retention_streaming':8*W*Z*2,'prefix32_input_retention_streaming':32*W*Z*2,'prefix100_input_retention_streaming':100*W*Z*2},'historical_energy_sensitivity':{'processing_energy_Wh':2.35*520/3600,'buffer_energy_Wh':2.43*2418/3600,'extra_byte_fraction_offset_by20percent_processing_reduction':0.2*2.35*520/(2.43*2418)},'timing_exclusions':['raw input file/network I/O','layout conversion to assumed native source layout','context allocation','header construction','compressed output file/telemetry I/O','DMA/backpressure/interference','downlink contact scheduling'],'warnings':['Host Clang18 MCJIT medians are not flight measurements','Native BIP line bursts are a coarse arrival envelope; intraline readout not measured','Streaming overlap is analytic, current code uses resident replay','CHIME envelope is 2020 predevelopment and uses near-lossless/block coder; not a claim this profile meets CHIME requirements']}
print(json.dumps(accounting),flush=True)
print(json.dumps({'kind':'evidence-inventory','full_adaptive_cases':len(full_results),'fixed_calibration_cases':len(fixed_results),'BIL_prefix_cases':len(bil_results),'two_image_cases':len(segmented_results),'independent_nu9_prefix_checks':2*len(reference_checks),'independent_nu4_prefix_checks':1,'all_retained':True,'baseline_source_sha256':hashlib.sha256(csrc2.encode()).hexdigest(),'files_written_after_permission_change':False}),flush=True)
print('ACCOUNTING_COMPLETE',flush=True)

