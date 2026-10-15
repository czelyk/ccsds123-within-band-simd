#define _POSIX_C_SOURCE 200809L
#include "core.h"
#ifndef BARE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#endif
#if defined(BARE)||defined(RVV_NATIVE)
#define VECTOR_RVV
#include <riscv_vector.h>
#else
#include <immintrin.h>
#endif
typedef struct {int width,height,bands,local,nu_max,is_fixed,bil;size_t n,golden_n,received_rows,first_row_after_received;uint16_t*raw,*ring;const uint16_t*cur[128],*prev[128];uint8_t*golden,*output;int32_t*scratch,*band_scratch,*predictions;int32_t fixed_weights[128][6];int group,layout,learn_only;int32_t *endweights;uint64_t *trace;size_t trace_n;} Frame;
typedef struct {uint8_t*p;uint64_t bits;unsigned fill;} Writer;
static inline void put(Writer*w,uint64_t v,unsigned n){
    w->bits=(w->bits<<n)|v;w->fill+=n;
    while(w->fill>=8){w->fill-=8;*w->p++=(uint8_t)(w->bits>>w->fill);}
    if(w->fill)w->bits&=(1ull<<w->fill)-1;else w->bits=0;
}
static inline unsigned mapped(int32_t s,int32_t doublep){
    int p=doublep>>1,e=s-p,a=e<0?-e:e,theta=p<65535-p?p:65535-p;
    if(a>theta)return a+theta;
    return 2*a-(((doublep&1)?-e:e)<0);
}
typedef struct {unsigned count,acc,previous;} Entropy;
static inline void encode(Writer*w,Entropy*e,unsigned delta,size_t t){
    if(!t){put(w,delta,16);return;}
    if(t>1){if(e->count==255){e->count=(e->count+1)>>1;e->acc=(e->acc+e->previous+1)>>1;}
        else {e->count++;e->acc+=e->previous;}}
    unsigned a=e->acc+((49*e->count)>>7),k=0;
    if(a>=2*e->count){k=__builtin_clz(e->count)-__builtin_clz(a);if(((uint64_t)e->count<<k)>a)k--;if(k>14)k=14;}
    unsigned q=delta>>k;
    if(q<32)put(w,(1ull<<k)|(delta&((1u<<k)-1)),q+1+k);
    else put(w,delta,48);
    e->previous=delta;
}
/* In BIL mode the fixture reader is a replay source. Only arriving rows
 * enter the encoder's two-line ring; the predictor reads these row views.
 * A real DMA/front-end can replace the row copy without changing kernels. */

static uint64_t tick(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;}
static void trace_row(Frame*f,Writer*bw,int y,int z,int first,int last,uint64_t begin){
 if(!f->trace)return;
 uint64_t*q=f->trace+8*f->trace_n++;
 q[0]=y;q[1]=z;q[2]=first;q[3]=last;q[4]=begin;q[5]=tick();q[6]=bw->p-f->output;q[7]=bw->fill;
}
static void prepare_group(Frame*f,int y,int first,int lanes){
 for(int z=first;z<first+lanes;z++){
  f->cur[z]=f->ring+((size_t)2*z+(y&1))*f->width;
  f->prev[z]=f->ring+((size_t)2*z+((y+1)&1))*f->width;
 }
 if(f->layout){
  for(int x=0;x<f->width;x++)for(int z=first;z<first+lanes;z++)
   ((uint16_t*)f->cur[z])[x]=f->raw[((size_t)y*f->width+x)*f->bands+z];
 }else{
  for(int z=first;z<first+lanes;z++)memcpy((uint16_t*)f->cur[z],f->raw+((size_t)y*f->bands+z)*f->width,f->width*2);
 }
 f->received_rows+=lanes;
}
static void prepare_rows(Frame*f,int y,int arriving_band){
 if(f->bil){prepare_group(f,y,arriving_band<0?0:arriving_band,arriving_band<0?f->bands:1);return;}
 for(int z=0;z<f->bands;z++){f->cur[z]=f->raw+z*f->n+(size_t)y*f->width;f->prev[z]=y?f->cur[z]-f->width:f->cur[z];}
}
static inline int sum(const Frame*f,int z,int x,int y){
    const uint16_t*p=f->cur[z],*above=f->prev[z];int w=f->width;
    if(f->local==3){if(y)return 4*above[x];return z?4*f->cur[z-1][x-1]:131072;}
    if(!y)return 4*p[x-1];
    if(!x)return 2*(above[x]+above[x+1]);
    if(x==w-1)return p[x-1]+above[x-1]+2*above[x];
    return p[x-1]+above[x-1]+above[x]+above[x+1];
}
static inline int local_values(const Frame*f,int z,int x,int y,int*u){
    const uint16_t*p=f->cur[z],*above=f->prev[z];int sigma=sum(f,z,x,y);
    if(y){u[0]=4*above[x]-sigma;u[1]=x?4*p[x-1]-sigma:u[0];u[2]=x?4*above[x-1]-sigma:u[0];}
    else u[0]=u[1]=u[2]=0;
    for(int i=0;i<z&&i<3;i++){
        int q=z-i-1;u[3+i]=4*f->cur[q][x]-sum(f,q,x,y);
    }
    return sigma;
}
static inline int scaling(size_t t,int width,int nu_max){int v=-1+(int)((long)t-width)/64;if((long)t-width<0)v=-1;if(v<-1)v=-1;if(v>nu_max)v=nu_max;return v-3;}
static inline int32_t clamp(int64_t a,int lo,int hi){return a<lo?lo:a>hi?hi:(int32_t)a;}
static void init(int32_t*w,int c){for(int i=0;i<6;i++)w[i]=0;if(c>3){w[3]=458752;for(int i=4;i<c;i++)w[i]=w[i-1]/8;}}
/* Separate fused implementations let the compiler specialize and unroll
 * the short dot product, avoiding an artificially weak dynamic-C baseline. */
#define FUSED_IMPL(N,NAME,EAGER) static void NAME(Frame*f,int z,int y,Writer*bw,int32_t*weights,Entropy*e){ \
    for(int x=(!y);x<f->width;x++){ \
        size_t t=(size_t)y*f->width+x;int u[6],sigma=local_values(f,z,x,y,u),r=scaling(t,f->width,f->nu_max); \
        int64_t d=(int64_t)sigma*524288+1048576; \
        for(int i=0;i<N;i++)d+=(int64_t)u[i]*weights[i]; \
        int32_t wp[N],wm[N]; \
        if(EAGER)for(int i=0;i<N;i++){int64_t a=u[i],b=-(int64_t)u[i];a=r>=0?a>>r:a*((int64_t)1<<-r);b=r>=0?b>>r:b*((int64_t)1<<-r);wp[i]=clamp(weights[i]+((a+1)>>1),-2097152,2097151);wm[i]=clamp(weights[i]+((b+1)>>1),-2097152,2097151);} \
        int p=clamp(d>>20,0,131071),s=2*f->cur[z][x]>=p?1:-1; \
        for(int i=0;i<N;i++){if(EAGER)weights[i]=s==1?wp[i]:wm[i];else{int64_t a=(int64_t)s*u[i];a=r>=0?a>>r:a*((int64_t)1<<-r);weights[i]=clamp(weights[i]+((a+1)>>1),-2097152,2097151);}} \
        if(!f->learn_only)encode(bw,e,mapped(f->cur[z][x],p),t); \
    }}
#define FUSED(N) FUSED_IMPL(N,fused##N,0) FUSED_IMPL(N,eager##N,1)
FUSED(3) FUSED(4) FUSED(5) FUSED(6)
static void (*fused[4])(Frame*,int,int,Writer*,int32_t*,Entropy*)={fused3,fused4,fused5,fused6};
static void (*eager[4])(Frame*,int,int,Writer*,int32_t*,Entropy*)={eager3,eager4,eager5,eager6};
static Kernel scalars[]={scalar3,scalar4,scalar5,scalar6};
#ifdef VECTOR_RVV
static Kernel avxs[]={rvv3,rvv4,rvv5,rvv6};
#else
static Kernel avxs[]={avx3,avx4,avx5,avx6};
#endif
static Kernel fixed_kernels[]={frozen3,frozen4,frozen5,frozen6};
#ifdef VECTOR_RVV
#include "band_rvv.inc"
#else
/* Conventional SIMD across independent bands, with the whole cube available.
 * Padding inactive lanes is explicit. No speculative work or fallback. */

static void band_parallel(Frame*f,Writer*writers,Entropy*states){
 int32_t wi[6][136]={{0}};
 for(int z=0;z<f->bands;z++)for(int i=3;i<3+(z<3?z:3);i++)wi[i][z]=i==3?458752:wi[i-1][z]/8;
 for(int y=0;y<f->height;y++)for(int zbase=0;zbase<f->bands;zbase+=f->group){
  int lanes=f->bands-zbase;if(lanes>f->group)lanes=f->group;
  uint64_t begin=f->trace?tick():0;
  prepare_group(f,y,zbase,lanes);
  __m256i weights[6],zero=_mm256_setzero_si256(),one=_mm256_set1_epi32(1),low=_mm256_set1_epi32(-2097152),high=_mm256_set1_epi32(2097151);
  for(int i=0;i<6;i++)weights[i]=_mm256_loadu_si256((void*)(wi[i]+zbase));
        int x0=!y;
        for(int x=x0;x<f->width;x++)for(int lane=0;lane<8;lane++){
            int z=zbase+lane;
            int u[6]={0},sigma=0;
            if(lane<lanes)sigma=local_values(f,z,x,y,u);
            for(int i=0;i<6;i++)f->band_scratch[(7*(size_t)x+i)*8+lane]=u[i];
            f->band_scratch[(7*(size_t)x+6)*8+lane]=sigma;
        }
        for(int x=x0;x<f->width;x++){
            size_t t=(size_t)y*f->width+x;int r=scaling(t,f->width,f->nu_max);__m256i u[6];
            __m256i d0=_mm256_set1_epi64x(1048576),d1=d0;
            for(int i=0;i<6;i++){
                u[i]=_mm256_loadu_si256((void*)(f->band_scratch+(7*(size_t)x+i)*8));
                d0=_mm256_add_epi64(d0,_mm256_mul_epi32(_mm256_cvtepi32_epi64(_mm256_castsi256_si128(u[i])),_mm256_cvtepi32_epi64(_mm256_castsi256_si128(weights[i]))));
                d1=_mm256_add_epi64(d1,_mm256_mul_epi32(_mm256_cvtepi32_epi64(_mm256_extracti128_si256(u[i],1)),_mm256_cvtepi32_epi64(_mm256_extracti128_si256(weights[i],1))));
            }
            __m256i sigma=_mm256_loadu_si256((void*)(f->band_scratch+(7*(size_t)x+6)*8));
            d0=_mm256_add_epi64(d0,_mm256_slli_epi64(_mm256_cvtepi32_epi64(_mm256_castsi256_si128(sigma)),19));
            d1=_mm256_add_epi64(d1,_mm256_slli_epi64(_mm256_cvtepi32_epi64(_mm256_extracti128_si256(sigma,1)),19));
            __m256i neg0=_mm256_cmpgt_epi64(zero,d0),neg1=_mm256_cmpgt_epi64(zero,d1),mx=_mm256_set1_epi64x(131071);
            d0=_mm256_blendv_epi8(_mm256_srli_epi64(d0,20),zero,neg0);d1=_mm256_blendv_epi8(_mm256_srli_epi64(d1,20),zero,neg1);
            d0=_mm256_blendv_epi8(d0,mx,_mm256_cmpgt_epi64(d0,mx));d1=_mm256_blendv_epi8(d1,mx,_mm256_cmpgt_epi64(d1,mx));
            __m256i order=_mm256_setr_epi32(0,2,4,6,0,2,4,6);
            __m256i p=_mm256_permutevar8x32_epi32(d0,order),p1=_mm256_permutevar8x32_epi32(d1,order);
            p=_mm256_inserti128_si256(p,_mm256_castsi256_si128(p1),1);
            int32_t pp[8],actual[8]={0};_mm256_storeu_si256((void*)pp,p);
            for(int lane=0;lane<lanes;lane++){int z=zbase+lane;f->predictions[lane*f->width+x]=pp[lane];actual[lane]=2*f->cur[z][x];}
            __m256i signs=_mm256_blendv_epi8(one,_mm256_set1_epi32(-1),_mm256_cmpgt_epi32(p,_mm256_loadu_si256((void*)actual)));
            __m256i shr=_mm256_set1_epi32(r>0?r:0),shl=_mm256_set1_epi32(r<0?-r:0);
            for(int i=0;i<6;i++){
                __m256i a=_mm256_mullo_epi32(u[i],signs);a=_mm256_srav_epi32(_mm256_sllv_epi32(a,shl),shr);
                a=_mm256_srai_epi32(_mm256_add_epi32(a,one),1);weights[i]=_mm256_min_epi32(high,_mm256_max_epi32(low,_mm256_add_epi32(weights[i],a)));
            }
        }
        for(int z=zbase;z<zbase+lanes;z++){
            Writer*dest=f->bil?writers:writers+z;
            if(f->bil&&!y)encode(dest,states+z,mapped(f->cur[z][0],z?2*f->cur[z-1][0]:65536),0);
            for(int x=x0;x<f->width;x++){size_t t=(size_t)y*f->width+x;encode(dest,states+z,mapped(f->cur[z][x],f->predictions[(z-zbase)*f->width+x]),t);}
            if(f->bil&&!y&&!z)f->first_row_after_received=f->received_rows;
            trace_row(f,dest,y,z,zbase,zbase+lanes,begin);
        }

  for(int i=0;i<6;i++){int32_t tmp[8];_mm256_storeu_si256((void*)tmp,weights[i]);for(int lane=0;lane<lanes;lane++)wi[i][zbase+lane]=tmp[lane];}
 }
}

static void band_parallel_compact(Frame*f,Writer*writers,Entropy*states){
 int32_t wi[6][136]={{0}};
 for(int z=0;z<f->bands;z++)for(int i=3;i<3+(z<3?z:3);i++)wi[i][z]=i==3?458752:wi[i-1][z]/8;
 for(int y=0;y<f->height;y++)for(int zbase=0;zbase<f->bands;zbase+=f->group){
  int lanes=f->bands-zbase;if(lanes>f->group)lanes=f->group;
  uint64_t begin=f->trace?tick():0;
  prepare_group(f,y,zbase,lanes);
  __m256i weights[6],zero=_mm256_setzero_si256(),one=_mm256_set1_epi32(1),low=_mm256_set1_epi32(-2097152),high=_mm256_set1_epi32(2097151);
  for(int i=0;i<6;i++)weights[i]=_mm256_loadu_si256((void*)(wi[i]+zbase));
        int x0=!y;
        for(int x=x0;x<f->width;x++){
int32_t features[7*8];
for(int lane=0;lane<8;lane++){
            int z=zbase+lane;
            int u[6]={0},sigma=0;
            if(lane<lanes)sigma=local_values(f,z,x,y,u);
            for(int i=0;i<6;i++)features[i*8+lane]=u[i];
            features[6*8+lane]=sigma;
        }
        
            size_t t=(size_t)y*f->width+x;int r=scaling(t,f->width,f->nu_max);__m256i u[6];
            __m256i d0=_mm256_set1_epi64x(1048576),d1=d0;
            for(int i=0;i<6;i++){
                u[i]=_mm256_loadu_si256((void*)(features+i*8));
                d0=_mm256_add_epi64(d0,_mm256_mul_epi32(_mm256_cvtepi32_epi64(_mm256_castsi256_si128(u[i])),_mm256_cvtepi32_epi64(_mm256_castsi256_si128(weights[i]))));
                d1=_mm256_add_epi64(d1,_mm256_mul_epi32(_mm256_cvtepi32_epi64(_mm256_extracti128_si256(u[i],1)),_mm256_cvtepi32_epi64(_mm256_extracti128_si256(weights[i],1))));
            }
            __m256i sigma=_mm256_loadu_si256((void*)(features+6*8));
            d0=_mm256_add_epi64(d0,_mm256_slli_epi64(_mm256_cvtepi32_epi64(_mm256_castsi256_si128(sigma)),19));
            d1=_mm256_add_epi64(d1,_mm256_slli_epi64(_mm256_cvtepi32_epi64(_mm256_extracti128_si256(sigma,1)),19));
            __m256i neg0=_mm256_cmpgt_epi64(zero,d0),neg1=_mm256_cmpgt_epi64(zero,d1),mx=_mm256_set1_epi64x(131071);
            d0=_mm256_blendv_epi8(_mm256_srli_epi64(d0,20),zero,neg0);d1=_mm256_blendv_epi8(_mm256_srli_epi64(d1,20),zero,neg1);
            d0=_mm256_blendv_epi8(d0,mx,_mm256_cmpgt_epi64(d0,mx));d1=_mm256_blendv_epi8(d1,mx,_mm256_cmpgt_epi64(d1,mx));
            __m256i order=_mm256_setr_epi32(0,2,4,6,0,2,4,6);
            __m256i p=_mm256_permutevar8x32_epi32(d0,order),p1=_mm256_permutevar8x32_epi32(d1,order);
            p=_mm256_inserti128_si256(p,_mm256_castsi256_si128(p1),1);
            int32_t pp[8],actual[8]={0};_mm256_storeu_si256((void*)pp,p);
            for(int lane=0;lane<lanes;lane++){int z=zbase+lane;f->predictions[lane*f->width+x]=pp[lane];actual[lane]=2*f->cur[z][x];}
            __m256i signs=_mm256_blendv_epi8(one,_mm256_set1_epi32(-1),_mm256_cmpgt_epi32(p,_mm256_loadu_si256((void*)actual)));
            __m256i shr=_mm256_set1_epi32(r>0?r:0),shl=_mm256_set1_epi32(r<0?-r:0);
            for(int i=0;i<6;i++){
                __m256i a=_mm256_mullo_epi32(u[i],signs);a=_mm256_srav_epi32(_mm256_sllv_epi32(a,shl),shr);
                a=_mm256_srai_epi32(_mm256_add_epi32(a,one),1);weights[i]=_mm256_min_epi32(high,_mm256_max_epi32(low,_mm256_add_epi32(weights[i],a)));
            }
        }
        for(int z=zbase;z<zbase+lanes;z++){
            Writer*dest=f->bil?writers:writers+z;
            if(f->bil&&!y)encode(dest,states+z,mapped(f->cur[z][0],z?2*f->cur[z-1][0]:65536),0);
            for(int x=x0;x<f->width;x++){size_t t=(size_t)y*f->width+x;encode(dest,states+z,mapped(f->cur[z][x],f->predictions[(z-zbase)*f->width+x]),t);}
            if(f->bil&&!y&&!z)f->first_row_after_received=f->received_rows;
            trace_row(f,dest,y,z,zbase,zbase+lanes,begin);
        }

  for(int i=0;i<6;i++){int32_t tmp[8];_mm256_storeu_si256((void*)tmp,weights[i]);for(int lane=0;lane<lanes;lane++)wi[i][zbase+lane]=tmp[lane];}
 }
}

#endif
#include "tap_baseline.inc"
#include "native_bip.inc"
static size_t native_bip_scalar(Frame*f,int component_lmul){
    if(f->layout!=1)return UINT64_MAX;
    Writer bw={f->output,0,0};Entropy states[128];int32_t weights[128][6];
    for(int z=0;z<f->bands;z++){init(weights[z],3+(z<3?z:3));states[z]=(Entropy){8,44,0};}
    for(int y=0;y<f->height;y++)for(int x=0;x<f->width;x++)for(int z=0;z<f->bands;z++){
        size_t t=(size_t)y*f->width+x;int s=bip_sample(f,y,x,z),p;
        if(!t){p=z?2*bip_sample(f,y,x,z-1):65536;}
        else{
            int32_t u[6]={0};int sigma=bip_values(f,z,x,y,u),c=3+(z<3?z:3),r=scaling(t,f->width,f->nu_max);
            (void)component_lmul;{
                int64_t d=(int64_t)sigma*524288+1048576;
                for(int i=0;i<c;i++)d+=(int64_t)u[i]*weights[z][i];
                p=clamp(d>>20,0,131071);int sign=2*s>=p?1:-1;
                for(int i=0;i<c;i++){int64_t a=(int64_t)u[i]*sign;a=r>=0?a>>r:a*((int64_t)1<<-r);weights[z][i]=clamp(weights[z][i]+((a+1)>>1),-2097152,2097151);}
            }
        }
        encode(&bw,states+z,mapped(s,p),t);
    }
    if(f->endweights)memcpy(f->endweights,weights,f->bands*6*sizeof(int32_t));
    if(bw.fill)*bw.p++=(uint8_t)(bw.bits<<(8-bw.fill));return bw.p-f->output;
}

static size_t run(Frame*f,int variant,Counts*counts){
if(variant==11)return native_bip_scalar(f,0);
if(variant==9)return native_bip(f);
    Writer bw={f->output,0,0};f->received_rows=0;f->first_row_after_received=0;
    if(variant==3||variant==7){
        /* Keep one row of predictions and independent entropy states.
         * Write into disjoint worst-case band output reservations, then
         * concatenate their bitstrings in place. No full-frame residual
         * array is intrinsically required by this alternative. */
        Writer writers[128];Entropy states[128];size_t bits[128];
        if(f->bil){
            for(int z=0;z<f->bands;z++)states[z]=(Entropy){8,44,0};
            if(variant==7)band_parallel_compact(f,&bw,states);else band_parallel(f,&bw,states);
            if(bw.fill)*bw.p++=(uint8_t)(bw.bits<<(8-bw.fill));return bw.p-f->output;
        }
        for(int z=0;z<f->bands;z++){writers[z]=(Writer){f->output+z*f->n*6,0,0};states[z]=(Entropy){8,44,0};encode(writers+z,states+z,mapped(f->raw[z*f->n],z?2*f->raw[(z-1)*f->n]:65536),0);}
        if(variant==7)band_parallel_compact(f,writers,states);else band_parallel(f,writers,states);
        for(int z=0;z<f->bands;z++){bits[z]=(writers[z].p-(f->output+z*f->n*6))*8+writers[z].fill;if(writers[z].fill)*writers[z].p=(uint8_t)(writers[z].bits<<(8-writers[z].fill));}
        for(int z=0;z<f->bands;z++){const uint8_t*src=f->output+z*f->n*6;size_t left=bits[z];while(left>=8){put(&bw,*src++,8);left-=8;}if(left)put(&bw,*src>>(8-left),left);}
        if(bw.fill)*bw.p++=(uint8_t)(bw.bits<<(8-bw.fill));return bw.p-f->output;
    }
    int32_t weights[128][6];Entropy states[128];
    for(int z=0;z<f->bands;z++){int c=3+(z<3?z:3);init(weights[z],c);states[z]=(Entropy){8,44,0};if(variant==4||variant==6)for(int i=0;i<c;i++)weights[z][i]=f->fixed_weights[z][i];}
    int outer_limit=f->bil?f->height:f->bands,inner_limit=f->bil?f->bands:f->height;
    for(int outer=0;outer<outer_limit;outer++)for(int inner=0;inner<inner_limit;inner++){
        int z=f->bil?inner:outer,y=f->bil?outer:inner;
        uint64_t begin=f->trace?tick():0;
        prepare_rows(f,y,z);
        int c=3+(z<3?z:3);
        if(!f->learn_only&&!y)encode(&bw,states+z,mapped(f->cur[z][0],z?2*f->cur[z-1][0]:65536),0);
        if(variant==0||variant==5||variant==8){(variant==8?taps[c-3]:variant==0?fused[c-3]:eager[c-3])(f,z,y,&bw,weights[z],states+z);}
        else{
            int x0=!y,len=f->width-x0;Block b={0};b.n=len;
            for(int i=0;i<c;i++)b.u[i]=f->scratch+i*f->width;
            b.sigma=f->scratch+6*f->width;b.samples=f->scratch+7*f->width;b.rho=f->scratch+8*f->width;b.output=f->scratch+9*f->width;
            for(int j=0;j<len;j++){
                int u[6],x=x0+j;size_t t=(size_t)y*f->width+x;
                ((int*)b.sigma)[j]=local_values(f,z,x,y,u);
                for(int i=0;i<c;i++)((int*)b.u[i])[j]=u[i];
                ((int*)b.samples)[j]=f->cur[z][x];((int*)b.rho)[j]=scaling(t,f->width,f->nu_max);
            }
            if(variant==6){for(int j=0;j<len;j++){int64_t d=(int64_t)b.sigma[j]*4096+8192;for(int i=0;i<c;i++)d+=(int64_t)b.u[i][j]*weights[z][i];b.output[j]=clamp(d>>13,0,131071);}}else
            if(variant==4)fixed_kernels[c-3](&b,weights[z],counts);else
            (variant==1?scalars[c-3]:avxs[c-3])(&b,weights[z],counts);
            for(int j=0;j<len;j++)encode(&bw,states+z,mapped(b.samples[j],b.output[j]),(size_t)y*f->width+x0+j);
        }
        if(f->bil&&!y&&!z)f->first_row_after_received=f->received_rows;
        trace_row(f,&bw,y,z,z,z+1,begin);
    }
    if(f->endweights)memcpy(f->endweights,weights,(size_t)f->bands*6*sizeof(int32_t));
    if(f->learn_only)return 0;
    if(bw.fill)*bw.p++=(uint8_t)(bw.bits<<(8-bw.fill));
    return bw.p-f->output;
}

void* make_context(uint16_t*raw,int width,int height,int bands,int local,int nu,int layout){
 if(width<2||height<1||bands<1||bands>128)return 0;
 Frame*f=calloc(1,sizeof(Frame));f->raw=raw;f->width=width;f->height=height;f->bands=bands;f->local=local;f->nu_max=nu;f->n=(size_t)width*height;f->bil=1;f->layout=layout;
 f->scratch=aligned_alloc(64,((40*width+63)/64)*64);f->band_scratch=calloc((size_t)7*width*8,4);f->predictions=malloc((size_t)width*8*4);f->ring=calloc((size_t)2*width*bands,2);
 return f;
}
uint64_t compute(void*v,int variant,int group,int learn_lines,int32_t*weights,uint8_t*out,uint64_t*counts,uint64_t*trace){
 Frame*f=v;int full_height=(int)(f->n/f->width);f->height=learn_lines?learn_lines:full_height;f->learn_only=learn_lines!=0;f->output=out;f->group=group;f->trace=trace;f->trace_n=0;f->endweights=(learn_lines||variant==0||variant==9)?weights:0;
 if(variant==4||variant==6)for(int z=0;z<f->bands;z++)for(int i=0;i<6;i++)f->fixed_weights[z][i]=weights[z*6+i];
 Counts c={0};size_t n=run(f,variant,&c);counts[0]=c.accepted;counts[1]=c.rejected;counts[2]=f->first_row_after_received;counts[3]=f->trace_n;
 f->height=full_height;return n;
}
void free_context(void*v){Frame*f=v;free(f->scratch);free(f->band_scratch);free(f->predictions);free(f->ring);free(f);}
