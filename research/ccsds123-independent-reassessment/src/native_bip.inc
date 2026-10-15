/* Established spectral SIMD, native BIP source AND BIP compressed ordering.
 * This is a baseline, not a new codec or scientific contribution.
 * Each band's predictor and entropy state see the same spatial sequence.
 * No complete feature/prediction row and no BIP-to-BIL gather are used.
 */
static inline int bip_sample(Frame*f,int y,int x,int z){
    return f->raw[((size_t)y*f->width+x)*f->bands+z];
}
static inline int bip_sum(Frame*f,int z,int x,int y){
    if(f->local==3){if(y)return 4*bip_sample(f,y-1,x,z);return z?4*bip_sample(f,y,x-1,z-1):131072;}
    if(!y)return 4*bip_sample(f,y,x-1,z);
    if(!x)return 2*(bip_sample(f,y-1,x,z)+bip_sample(f,y-1,x+1,z));
    if(x==f->width-1)return bip_sample(f,y,x-1,z)+bip_sample(f,y-1,x-1,z)+2*bip_sample(f,y-1,x,z);
    return bip_sample(f,y,x-1,z)+bip_sample(f,y-1,x-1,z)+bip_sample(f,y-1,x,z)+bip_sample(f,y-1,x+1,z);
}
static inline int bip_values(Frame*f,int z,int x,int y,int*u){
    int sigma=bip_sum(f,z,x,y);
    if(y){u[0]=4*bip_sample(f,y-1,x,z)-sigma;u[1]=x?4*bip_sample(f,y,x-1,z)-sigma:u[0];u[2]=x?4*bip_sample(f,y-1,x-1,z)-sigma:u[0];}
    else u[0]=u[1]=u[2]=0;
    for(int i=0;i<z&&i<3;i++){int q=z-i-1;u[3+i]=4*bip_sample(f,y,x,q)-bip_sum(f,q,x,y);}
    return sigma;
}
static size_t native_bip(Frame*f){
    if(f->layout!=1)return UINT64_MAX;
    Writer bw={f->output,0,0};Entropy states[128];int32_t wi[6][136]={{0}};
    for(int z=0;z<f->bands;z++){
        states[z]=(Entropy){8,44,0};
        for(int i=3;i<3+(z<3?z:3);i++)wi[i][z]=i==3?458752:wi[i-1][z]/8;
    }
    __m256i zero=_mm256_setzero_si256(),one=_mm256_set1_epi32(1),low=_mm256_set1_epi32(-2097152),high=_mm256_set1_epi32(2097151);
    for(int y=0;y<f->height;y++)for(int x=0;x<f->width;x++){
        size_t t=(size_t)y*f->width+x;
        if(!t){for(int z=0;z<f->bands;z++)encode(&bw,states+z,mapped(bip_sample(f,y,x,z),z?2*bip_sample(f,y,x,z-1):65536),0);continue;}
        int r=scaling(t,f->width,f->nu_max);
        for(int zbase=0;zbase<f->bands;zbase+=f->group){
            int lanes=f->bands-zbase;if(lanes>f->group)lanes=f->group;
            uint64_t begin=f->trace&&f->trace_n<512?tick():0;
            int32_t features[7][8]={{0}},actual[8]={0},pp[8];__m256i weights[6],u[6];
            for(int lane=0;lane<lanes;lane++){
                int values[6]={0},z=zbase+lane;
                features[6][lane]=bip_values(f,z,x,y,values);actual[lane]=2*bip_sample(f,y,x,z);
                for(int i=0;i<6;i++)features[i][lane]=values[i];
            }
            __m256i d0=_mm256_set1_epi64x(1048576),d1=d0;
            for(int i=0;i<6;i++){
                weights[i]=_mm256_loadu_si256((void*)(wi[i]+zbase));u[i]=_mm256_loadu_si256((void*)features[i]);
                d0=_mm256_add_epi64(d0,_mm256_mul_epi32(_mm256_cvtepi32_epi64(_mm256_castsi256_si128(u[i])),_mm256_cvtepi32_epi64(_mm256_castsi256_si128(weights[i]))));
                d1=_mm256_add_epi64(d1,_mm256_mul_epi32(_mm256_cvtepi32_epi64(_mm256_extracti128_si256(u[i],1)),_mm256_cvtepi32_epi64(_mm256_extracti128_si256(weights[i],1))));
            }
            __m256i sigma=_mm256_loadu_si256((void*)features[6]);
            d0=_mm256_add_epi64(d0,_mm256_slli_epi64(_mm256_cvtepi32_epi64(_mm256_castsi256_si128(sigma)),19));
            d1=_mm256_add_epi64(d1,_mm256_slli_epi64(_mm256_cvtepi32_epi64(_mm256_extracti128_si256(sigma,1)),19));
            __m256i mx=_mm256_set1_epi64x(131071),neg0=_mm256_cmpgt_epi64(zero,d0),neg1=_mm256_cmpgt_epi64(zero,d1);
            d0=_mm256_blendv_epi8(_mm256_srli_epi64(d0,20),zero,neg0);d1=_mm256_blendv_epi8(_mm256_srli_epi64(d1,20),zero,neg1);
            d0=_mm256_blendv_epi8(d0,mx,_mm256_cmpgt_epi64(d0,mx));d1=_mm256_blendv_epi8(d1,mx,_mm256_cmpgt_epi64(d1,mx));
            __m256i order=_mm256_setr_epi32(0,2,4,6,0,2,4,6),p=_mm256_permutevar8x32_epi32(d0,order),p1=_mm256_permutevar8x32_epi32(d1,order);
            p=_mm256_inserti128_si256(p,_mm256_castsi256_si128(p1),1);_mm256_storeu_si256((void*)pp,p);
            __m256i signs=_mm256_blendv_epi8(one,_mm256_set1_epi32(-1),_mm256_cmpgt_epi32(p,_mm256_loadu_si256((void*)actual)));
            for(int i=0;i<6;i++){
                __m256i a=_mm256_mullo_epi32(u[i],signs);
                if(r>=0)a=_mm256_sra_epi32(a,_mm_cvtsi32_si128(r));else a=_mm256_sll_epi32(a,_mm_cvtsi32_si128(-r));
                a=_mm256_srai_epi32(_mm256_add_epi32(a,one),1);
                weights[i]=_mm256_min_epi32(high,_mm256_max_epi32(low,_mm256_add_epi32(weights[i],a)));
                int32_t tmp[8];_mm256_storeu_si256((void*)tmp,weights[i]);for(int lane=0;lane<lanes;lane++)wi[i][zbase+lane]=tmp[lane];
            }
            for(int lane=0;lane<lanes;lane++)encode(&bw,states+zbase+lane,mapped(actual[lane]>>1,pp[lane]),t);
            if(f->trace&&f->trace_n<512){uint64_t*q=f->trace+8*f->trace_n++;q[0]=y;q[1]=x;q[2]=zbase;q[3]=zbase+lanes;q[4]=begin;q[5]=tick();q[6]=bw.p-f->output;q[7]=bw.fill;}
        }
    }
    if(f->endweights)for(int z=0;z<f->bands;z++)for(int i=0;i<6;i++)f->endweights[z*6+i]=wi[i][z];
    if(bw.fill)*bw.p++=(uint8_t)(bw.bits<<(8-bw.fill));return bw.p-f->output;
}
