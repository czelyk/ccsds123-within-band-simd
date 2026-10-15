from pathlib import Path
import json,csv,hashlib
R=Path(__file__).resolve().parent;E=R/'evidence'
records=[json.loads(l) for l in (E/'landsat-pilot.jsonl').read_text().splitlines()]
summaries=[x for x in records if x['kind']=='summary'];main=[x for x in summaries if not x['secondary']];held=[x for x in main if x['role']=='held-out-acquisition']
assert len(summaries)==9 and len(main)==8 and len(held)==6
rows=[]
for x in summaries:
 m=x['methods_ns'];best=min((t,k) for k,t in m.items() if k!='2:1');single=min(m[k] for k in ('0:1','8:1','11:1'))
 rows.append({'file':x['file'],'local':x['local'],'nu_max':x['nu_max'],'role':x['role'],'secondary':x['secondary'],'proposal_ns_sample':m['2:1'],'best_tested_baseline':best[1],'best_baseline_ns_sample':best[0],'best_baseline_time_over_proposal':best[0]/m['2:1'],'best_single_band_time_over_proposal':single/m['2:1'],'native_BIP8_time':m['9:8'],'total_bytes':x['total_bytes']})
with (E/'landsat-summary.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
fixed=[r for r in records if r['kind']=='fixed-summary'];stripes=[r for r in records if r['kind']=='independent-stripe-reset']
assert len(fixed)==16 and len(stripes)==24
checks=json.loads((E/'landsat8-publisher-checksums.json').read_text());downloads=json.loads((E/'landsat8-downloads.json').read_text())
assert len(downloads)==4
for d in downloads:assert d['md5']==next(c['publisher_md5'] for c in checks if c['id']==d['id'])
rvv=json.loads((E/'rvv-validation.json').read_text());assert len(rvv)==4 and all(r['pass'] for r in rvv)
def interval(items,key):return [min(x[key] for x in items),max(x[key] for x in items)]
mainrows=[r for r in rows if not r['secondary']];heldrows=[r for r in mainrows if r['role']=='held-out-acquisition']
result={'decision':'REVISE','scope':'processed L1 workload pilot and functional RVV comparator revision; no physical results','acquisitions':4,'held_out_acquisitions':3,'main_configuration_cases':8,'held_out_main_cases':6,'secondary_cases':1,'independent_adaptive_prefix_checks':sum(r['kind']=='independent-prefix' for r in records),'independent_default_fixed_prefix_checks':sum(r['kind']=='independent-fixed-prefix' for r in records),'raw_adaptive_timing_trials':sum(r['kind']=='timing' for r in records),'raw_fixed_timing_trials':sum(r['kind']=='fixed-timing' for r in records),'main_best_baseline_time_over_proposal_range':interval(mainrows,'best_baseline_time_over_proposal'),'held_out_best_baseline_time_over_proposal_range':interval(heldrows,'best_baseline_time_over_proposal'),'main_proposal_faster_than_best_tested_baseline_cases':sum(r['best_baseline_time_over_proposal']>1 for r in mainrows),'main_best_single_band_time_over_proposal_range':interval(mainrows,'best_single_band_time_over_proposal'),'fixed_size_change_ranges_percent':{name:interval([x for x in fixed if x['calibration']==name and not x['secondary'] and x['role']=='held-out-acquisition'],'size_change_percent') for name in ('default','earlier-acquisition-retrospective')},'stripe_size_change_ranges_percent':{str(n):interval([x for x in stripes if x['stripes']==n],'size_change_percent') for n in (2,4,8)},'stripe_parallel_performance_measured':False,'all_four_publisher_md5_match':True,'RVV':{'VLEN':[r['VLEN'] for r in rvv],'cases_per_VLEN':144,'method_checks_per_VLEN':2016,'mapped_residual_comparisons_per_VLEN':4249224,'mismatches':0,'scope':rvv[0]['scope']},'warnings':['Processed/calibrated data, not raw focal-plane data','Resident BIP transpose excluded from timing; no real source arrival claim','Retrospective calibrated products do not prove flight-time calibration availability','Omega11 fixed vs Omega19 adaptive also changes precision','Frequency not locked; three trials do not establish a mission-population interval','Stripe sizes omit mission-specific container/index/packet overhead','New RVV implementations are functional baselines, not proven architecture-optimal','Original proposal capped at eight samples; no unrestricted scaling claim','No physical time or energy measured','Actual operational workload/profile/budget and IAF eligibility remain unresolved'],'rows':rows}
(E/'revision-analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))

followup=[json.loads(l) for l in (E/'fixed12-followup.jsonl').read_text().splitlines()]
f12=[x for x in followup if x['kind']=='summary'];m12=[x for x in f12 if x['nu_max_training']==9]
assert len(f12)==7 and len(m12)==6
assert sum(x['kind']=='independent-prefix' for x in followup)==6
assert sum(x['kind']=='default-identity' for x in followup)==9
assert sum(x['kind']=='timing' for x in followup)==42
f12result={'independent_prefix_checks':6,'default_full_case_identities':9,'raw_custom_timing_trials':42,'held_out_main_calibrated_size_change_percent':interval(m12,'size_change_percent'),'secondary_calibrated_size_change_percent':next(x['size_change_percent'] for x in f12 if x['nu_max_training']==4),'arithmetic_bound':next(x for x in followup if x['kind']=='arithmetic-bound'),'initial_validation_error_preserved':True,'initial_error_reason':'The first-sample weight storage is unused; the original assertion included it. Active weights from t=1 were constant.','scope':'profile-specific stronger baseline, not claimed novelty; Omega12 vs adaptive Omega19 remains a precision change','rows':f12}
(E/'fixed12-analysis.json').write_text(json.dumps(f12result,indent=2)+'\n')
result['fixed12_followup']={k:v for k,v in f12result.items() if k!='rows'}
(E/'revision-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
