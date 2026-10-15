/* Conventional SIMD across predictor components for ONE sequential sample.
 * No predicted signs, prefix scan, speculative work, or fallback.
 * Exact 32x32 -> 64 products; integer reduction has no overflow in profile.
 */
static inline __attribute__((always_inline)) void tap_row(Frame*f,int z,int y,Writer*bw,int32_t*w,Entropy*e,int c){
    __m256i mask=_mm256_setr_epi32(c>0?-1:0,c>1?-1:0,c>2?-1:0,c>3?-1:0,c>4?-1:0,c>5?-1:0,0,0);
    __m256i weights=_mm256_maskload_epi32(w,mask),zero=_mm256_setzero_si256();
    const __m256i one=_mm256_set1_epi32(1),low=_mm256_set1_epi32(-2097152),high=_mm256_set1_epi32(2097151);
    for(int x=!y;x<f->width;x++){
        size_t t=(size_t)y*f->width+x;int32_t values[8]={0};
        int sigma=local_values(f,z,x,y,values),r=scaling(t,f->width,f->nu_max);
        __m256i u=_mm256_loadu_si256((const void*)values);
        __m256i even=_mm256_mul_epi32(u,weights);
        __m256i odd=_mm256_mul_epi32(_mm256_srli_epi64(u,32),_mm256_srli_epi64(weights,32));
        __m256i pairs=_mm256_add_epi64(even,odd);
        __m128i halves=_mm_add_epi64(_mm256_castsi256_si128(pairs),_mm256_extracti128_si256(pairs,1));
        int64_t d=(int64_t)sigma*524288+1048576+_mm_cvtsi128_si64(halves)+_mm_extract_epi64(halves,1);
        int p=clamp(d>>20,0,131071),positive=2*f->cur[z][x]>=p;
        __m256i a=positive?u:_mm256_sub_epi32(zero,u);
        if(r>=0)a=_mm256_sra_epi32(a,_mm_cvtsi32_si128(r));
        else a=_mm256_sll_epi32(a,_mm_cvtsi32_si128(-r));
        a=_mm256_srai_epi32(_mm256_add_epi32(a,one),1);
        weights=_mm256_min_epi32(high,_mm256_max_epi32(low,_mm256_add_epi32(weights,a)));
        encode(bw,e,mapped(f->cur[z][x],p),t);
    }
    _mm256_maskstore_epi32(w,mask,weights);
}
#define TAP_ROW(N) static void tap##N(Frame*f,int z,int y,Writer*bw,int32_t*w,Entropy*e){tap_row(f,z,y,bw,w,e,N);}
TAP_ROW(3) TAP_ROW(4) TAP_ROW(5) TAP_ROW(6)
static void (*taps[4])(Frame*,int,int,Writer*,int32_t*,Entropy*)={tap3,tap4,tap5,tap6};
