#include <immintrin.h>

#define FN unused_scalar_wrapper
#include "portable.inc"
#undef FN
#define FN AVX_NAME
static __m256i narrow(__m256i a,__m256i b){
    __m256i order=_mm256_setr_epi32(0,2,4,6,0,2,4,6);
    a=_mm256_permutevar8x32_epi32(a,order);b=_mm256_permutevar8x32_epi32(b,order);
    return _mm256_inserti128_si256(a,_mm256_castsi256_si128(b),1);
}
static __m256i pred8(const Block*b,size_t t,__m256i weights[C]){
    __m256i d0=_mm256_set1_epi64x(1<<(OMEGA+1)),d1=d0;
    for(int i=0;i<C;i++){
        __m256i uv=_mm256_loadu_si256((void*)(b->u[i]+t));
        __m256i u0=_mm256_cvtepi32_epi64(_mm256_castsi256_si128(uv));
        __m256i u1=_mm256_cvtepi32_epi64(_mm256_extracti128_si256(uv,1));
        __m256i w0=_mm256_cvtepi32_epi64(_mm256_castsi256_si128(weights[i]));
        __m256i w1=_mm256_cvtepi32_epi64(_mm256_extracti128_si256(weights[i],1));
        d0=_mm256_add_epi64(d0,_mm256_mul_epi32(w0,u0));d1=_mm256_add_epi64(d1,_mm256_mul_epi32(w1,u1));
    }
    __m256i sv=_mm256_loadu_si256((void*)(b->sigma+t));
    d0=_mm256_add_epi64(d0,_mm256_slli_epi64(_mm256_cvtepi32_epi64(_mm256_castsi256_si128(sv)),OMEGA));
    d1=_mm256_add_epi64(d1,_mm256_slli_epi64(_mm256_cvtepi32_epi64(_mm256_extracti128_si256(sv,1)),OMEGA));
    __m256i z=_mm256_setzero_si256(),mx=_mm256_set1_epi64x(131071);
    __m256i neg0=_mm256_cmpgt_epi64(z,d0),neg1=_mm256_cmpgt_epi64(z,d1);
    d0=_mm256_or_si256(_mm256_srli_epi64(d0,OMEGA+1),_mm256_slli_epi64(neg0,64-(OMEGA+1)));
    d1=_mm256_or_si256(_mm256_srli_epi64(d1,OMEGA+1),_mm256_slli_epi64(neg1,64-(OMEGA+1)));
    d0=_mm256_blendv_epi8(d0,z,neg0);d1=_mm256_blendv_epi8(d1,z,neg1);
    d0=_mm256_blendv_epi8(d0,mx,_mm256_cmpgt_epi64(d0,mx));d1=_mm256_blendv_epi8(d1,mx,_mm256_cmpgt_epi64(d1,mx));
    return narrow(d0,d1);
}
static __m256i signs8(const Block*b,size_t t,__m256i p){
    __m256i actual=_mm256_slli_epi32(_mm256_loadu_si256((void*)(b->samples+t)),1);
    __m256i bad=_mm256_cmpgt_epi32(p,actual);
    return _mm256_blendv_epi8(_mm256_set1_epi32(1),_mm256_set1_epi32(-1),bad);
}
/* Guess only: modular 32-bit arithmetic may be arbitrarily inaccurate.
 * Acceptance still requires the exact 64-bit predictor below. */
static __m256i approximate8(const Block*b,size_t t,const int32_t w[C]){
    const int shift=8;
    __m256i d=_mm256_setzero_si256();
    for(int i=0;i<C;i++)d=_mm256_add_epi32(d,_mm256_mullo_epi32(_mm256_set1_epi32(w[i]>>shift),_mm256_loadu_si256((void*)(b->u[i]+t))));
    __m256i s=_mm256_loadu_si256((void*)(b->sigma+t));
    d=_mm256_add_epi32(d,_mm256_slli_epi32(_mm256_and_si256(s,_mm256_set1_epi32(1)),OMEGA-shift));
    d=_mm256_add_epi32(d,_mm256_set1_epi32(1<<(OMEGA+1-shift)));
    d=_mm256_add_epi32(_mm256_srai_epi32(d,OMEGA+1-shift),_mm256_srai_epi32(s,1));
    return _mm256_min_epi32(_mm256_max_epi32(d,_mm256_setzero_si256()),_mm256_set1_epi32(131071));
}
static __m256i scan8(__m256i a){
    a=_mm256_add_epi32(a,_mm256_slli_si256(a,4));
    a=_mm256_add_epi32(a,_mm256_slli_si256(a,8));
    __m128i first=_mm256_castsi256_si128(a);
    first=_mm_shuffle_epi32(first,_MM_SHUFFLE(3,3,3,3));
    return _mm256_add_epi32(a,_mm256_inserti128_si256(_mm256_setzero_si256(),first,1));
}
void FN(const Block*b,int32_t*w,Counts*counts){
#ifdef FROZEN
    (void)counts;size_t t=0;__m256i ws[C];for(int i=0;i<C;i++)ws[i]=_mm256_set1_epi32(w[i]);
    for(;t+8<=b->n;t+=8)_mm256_storeu_si256((void*)(b->output+t),pred8(b,t,ws));
    for(;t<b->n;t++){int64_t d=(int64_t)b->sigma[t]*(1<<OMEGA)+(1<<(OMEGA+1));for(int i=0;i<C;i++)d+=(int64_t)b->u[i][t]*w[i];b->output[t]=clamp64(d>>(OMEGA+1),0,131071);}
#else
    size_t t=0;
    for(;t+8<=b->n;t+=8){
        __m256i ws[C],end[C],zero=_mm256_setzero_si256(),onev=_mm256_set1_epi32(1);
        for(int i=0;i<C;i++)ws[i]=_mm256_set1_epi32(w[i]);
        __m256i signs=signs8(b,t,approximate8(b,t,w));
        __m256i rr=_mm256_loadu_si256((void*)(b->rho+t));
        __m256i shr=_mm256_max_epi32(zero,rr),shl=_mm256_max_epi32(zero,_mm256_sub_epi32(zero,rr));
        __m256i invalid=zero;
        for(int i=0;i<C;i++){
            __m256i inc=_mm256_mullo_epi32(signs,_mm256_loadu_si256((void*)(b->u[i]+t)));
            inc=_mm256_srav_epi32(_mm256_sllv_epi32(inc,shl),shr);
            inc=_mm256_srai_epi32(_mm256_add_epi32(inc,onev),1);
            end[i]=_mm256_add_epi32(scan8(inc),_mm256_set1_epi32(w[i]));
            invalid=_mm256_or_si256(invalid,_mm256_cmpgt_epi32(_mm256_set1_epi32(WMIN),end[i]));
            invalid=_mm256_or_si256(invalid,_mm256_cmpgt_epi32(end[i],_mm256_set1_epi32(WMAX)));
            ws[i]=_mm256_sub_epi32(end[i],inc);
        }
        if(!_mm256_movemask_epi8(invalid)){
            __m256i p=pred8(b,t,ws);
            if(_mm256_movemask_epi8(_mm256_cmpeq_epi32(signs,signs8(b,t,p)))==-1){
                _mm256_storeu_si256((void*)(b->output+t),p);
                for(int i=0;i<C;i++)w[i]=_mm256_extract_epi32(end[i],7);
                counts->accepted++;continue;
            }
        }
        counts->rejected++;for(size_t j=t;j<t+8;j++)sample(b,j,w);
    }
    for(;t<b->n;t++)sample(b,t,w);
#endif
}
