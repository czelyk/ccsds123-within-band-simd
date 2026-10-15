from pathlib import Path
import json,statistics,hashlib,csv,math
import numpy as np
R=Path(__file__).resolve().parent;E=R/'evidence'
tap=[json.loads(l) for l in (E/'tap-comparison.jsonl').read_text().splitlines()]
bip=[json.loads(l) for l in (E/'native-bip-comparison.jsonl').read_text().splitlines()]
assert len([r for r in tap if r['kind']=='summary'])==10
assert len([r for r in bip if r['kind']=='summary'])==9
assert len([r for r in bip if r['kind']=='full-cube-residual-check'])==18
rows=[]
for r in tap:
    if r['kind']=='summary':
        m=r['methods_ns'];rows.append({'campaign':'tap','scene':r['file'].split('_2022')[0],'local':r['local'],'nu_max':r['nu_max'],'layout':r['layout'],'proposal_ns':m['2:1'],'scalar_ns':m['0:1'],'component_ns':m['8:1'],'band4_ns':m['7:4'],'band8_ns':m['7:8'],'speedup_best_single_band':min(m['0:1'],m['8:1'])/m['2:1']})
for r in bip:
    if r['kind']=='summary':
        m=r['methods_ns'];rows.append({'campaign':'bip','scene':r['file'].split('_2022')[0],'local':r['local'],'nu_max':r['nu_max'],'layout':'BIP','proposal_ns':m['2:1'],'BIL_band8_ns':m['7:8'],'BIP_band4_ns':m['9:4'],'BIP_band8_ns':m['9:8'],'native_BIP_speedup':m['2:1']/m['9:8'],'body_bytes':r['body_bytes']})
fields=list(dict.fromkeys(k for row in rows for k in row))
with (E/'comparison-summary.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
readiness=[];W=684;Z=120
for variant,group in ((0,1),(2,1),(7,2),(7,4),(7,8),(8,1)):
    a=np.load(E/f'trace-finnmark-local3-nu9-v{variant}-g{group}.npz')['trace']
    for Q in (256,1024,4096):
        row=a[np.searchsorted(a[:,6],Q)];y,z,first,last=map(int,row[:4])
        readiness.append({'path':f'v{variant}g{group}','body_quantum':Q,'y':y,'z':z,'input_samples_BIL':(y*Z+last)*W,'input_samples_BIP_for_same_row_staging':(y*W+W-1)*Z+last,'source':'implemented whole-row staging, not an intrinsic algorithm bound'})
a=np.load(E/'trace-native-BIP-local3-nu9-g8.npz')['trace']
for Q in (256,1024,4096):
    row=a[np.searchsorted(a[:,6],Q)];y,x,first,last=map(int,row[:4]);readiness.append({'path':'native-BIP-v9g8','body_quantum':Q,'y':y,'x':x,'input_samples_BIP':(y*W+x)*Z+last,'source':'causal source-prefix count inferred from actual access geometry; resident replay, not DMA test'})
main=[r for r in rows if r['campaign']=='tap' and r['nu_max']==9 and r['layout']=='BIP']
mainb=[r for r in rows if r['campaign']=='bip' and r['nu_max']==9]
aggregate={'main_acquisitions':4,'main_configuration_cases':8,'proposal_speedup_best_tested_single_band_range':[min(r['speedup_best_single_band'] for r in main),max(r['speedup_best_single_band'] for r in main)],'native_BIP_speedup_over_proposal_range':[min(r['native_BIP_speedup'] for r in mainb),max(r['native_BIP_speedup'] for r in mainb)],'native_BIP_faster_cases':sum(r['BIP_band8_ns']<r['proposal_ns'] for r in mainb),'independent_BIP_prefix_checks':3,'full_cube_residual_checks':18,'full_cube_comparisons_per_group':956*684*120,'new_timing_jobs_concurrent':False,'frequency_controlled':False,'all_negative_and_positive_trials_retained':True}
source=R/'original-source-manifest.json'
old=json.loads(source.read_text());checks={}
for p,digest in old.items():
    path=R/'src/reference_kernels'/p
    if path.exists():checks[p]=hashlib.sha256(path.read_bytes()).hexdigest()==digest
assert len(checks)==len(old) and all(checks.values()),'Historical source changed or missing'
summary={'aggregate':aggregate,'rows':rows,'output_readiness':readiness,'original_source_checks':checks,'warnings':['Four acquisitions, not eight independent scenes','Three or five host trials do not establish mission-population confidence intervals','BIP compressed order differs while every mapped residual, final weight and body byte count matches','No physical timing or energy measurements','Readiness counts are implementation-specific and do not establish a spacecraft deadline']}
(E/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'aggregate':aggregate,'readiness_1024':[r for r in readiness if r['body_quantum']==1024],'source_checks':checks},indent=2))
