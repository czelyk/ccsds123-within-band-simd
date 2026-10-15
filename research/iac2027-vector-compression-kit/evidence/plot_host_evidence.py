from pathlib import Path
import json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
kit=Path(__file__).resolve().parent.parent
rows=json.loads((kit/'evidence/final_results.json').read_text())
byname={Path(r['file']).name:r for r in rows}
def case(label):return byname[f'frame_{label}_nu9_NARROW_COLUMN_ORIENTED.bin']['medians_ns']
fig,axes=plt.subplots(1,2,figsize=(12,4.9),gridspec_kw={'width_ratios':[1.6,1]})
plt.rcParams.update({'font.size':10})
labels=['Indian Pines','Pavia University','Salinas'];codes=['pines','pavia','salinas']
styles=[('Best scalar/eager','#697786'),('Proposed','#087f8c'),('Band SIMD','#668ed1'),('Fixed weights*','#d89949')]
for k,(label,color) in enumerate(styles):
    values=[]
    for code in codes:
        med=case(code+'_bil')
        values.append(min(med[str(v)] for v in (0,1,5)) if k==0 else med[str(k+1)] if k<3 else case(code+'_bil_fixed')['4'])
    axes[0].bar(np.arange(3)+(k-1.5)*.19,values,.19,label=label,color=color)
axes[0].set(xticks=np.arange(3),xticklabels=labels,ylabel='Complete compressor time (ns / input sample)',title='Six-band line-interleaved processed crops')
axes[0].legend(frameon=False,ncol=2,loc='upper center',bbox_to_anchor=(.5,-.13),fontsize=9)
syn=['constant','checkerboard','noise']
speed=[min(case(s)[str(v)] for v in (0,1,5))/case(s)['2'] for s in syn]
axes[1].bar(np.arange(3),speed,color=['#ba655a' if v<1 else '#087f8c' for v in speed],width=.6)
axes[1].axhline(1,color='#3d4955',lw=1,ls='--')
for i,s in enumerate(speed):axes[1].text(i,s+.03,f'{s:.2f}×',ha='center')
axes[1].set(xticks=np.arange(3),xticklabels=['Constant','Checkerboard','Noise'],ylim=(0,1.25),ylabel='Speedup over best scalar/eager',title='Synthetic stress cases can be slower')
for ax in axes:
    ax.spines[['top','right']].set_visible(False);ax.set_axisbelow(True);ax.grid(axis='y',alpha=.18)
fig.suptitle('Host evidence only — i7-12700H, GCC13, pinned core; nine-trial medians',fontsize=12,y=.98)
fig.text(.5,.015,'*Fixed weights use different predictor parameters and a held-out spatial calibration crop. No embedded timing or energy measured.',ha='center',fontsize=9)
fig.subplots_adjust(bottom=.25,top=.83,wspace=.32,left=.07,right=.98)
fig.savefig(kit/'evidence/host-results.png',dpi=180)
fig.savefig(kit/'evidence/host-results.pdf')
