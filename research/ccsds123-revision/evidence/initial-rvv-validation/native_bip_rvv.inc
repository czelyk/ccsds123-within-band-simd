/* Native BIP order, conventional scalar/component/spectral execution.
 * BIP helper functions are copied unchanged from the independently checked
 * host baseline; arithmetic below is compared to a scalar BIP reference.
 */
static size_t native_bip_scalar(Frame*f,int component_lmul){
    if(f->layout!=1)return UINT64_MAX;
    Writer bw={f->output,0,0};Entropy states[128];int32_t weights[128][6];
    for(int z=0;z<f->bands;z++){init(weights[z],3+(z<3?z:3));states[z]=(Entropy){8,44,0};}
    for(int y=0;y<f->height;y++)for(int x=0;x<f->width;x++)for(int z=0;z<f->bands;z++){
        size_t t=(size_t)y*f->width+x;int s=bip_sample(f,y,x,z),p;
        if(!t){p=z?2*bip_sample(f,y,x,z-1):65536;}
        else{
            int32_t u[6]={0};int sigma=bip_values(f,z,x,y,u),c=3+(z<3?z:3),r=scaling(t,f->width,f->nu_max);
            if(component_lmul)p=component_update(u,sigma,2*s,weights[z],c,r,component_lmul);
            else{
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
static size_t native_bip(Frame*f){
    if(f->layout!=1)return UINT64_MAX;
    Writer bw={f->output,0,0};Entropy states[128];int32_t wi[6][128]={{0}};
    for(int z=0;z<f->bands;z++){
        states[z]=(Entropy){8,44,0};
        for(int i=3;i<3+(z<3?z:3);i++)wi[i][z]=i==3?458752:wi[i-1][z]/8;
    }
    for(int y=0;y<f->height;y++)for(int x=0;x<f->width;x++){
        size_t t=(size_t)y*f->width+x;
        if(!t){for(int z=0;z<f->bands;z++)encode(&bw,states+z,mapped(bip_sample(f,y,x,z),z?2*bip_sample(f,y,x,z-1):65536),0);continue;}
        for(int base=0;base<f->bands;){
            int request=f->bands-base;if(f->group>0&&request>f->group)request=f->group;
            size_t vl=__riscv_vsetvl_e32m1(request);
            int32_t features[7][128],actual[128],pp[128];
            for(size_t lane=0;lane<vl;lane++){
                int32_t u[6]={0};int z=base+lane;
                features[6][lane]=bip_values(f,z,x,y,u);actual[lane]=2*bip_sample(f,y,x,z);
                for(int i=0;i<6;i++)features[i][lane]=u[i];
            }
            spectral_step(features,actual,wi,base,scaling(t,f->width,f->nu_max),vl,pp);
            for(size_t lane=0;lane<vl;lane++)encode(&bw,states+base+lane,mapped(actual[lane]>>1,pp[lane]),t);
            base+=vl;
        }
    }
    if(f->endweights)for(int z=0;z<f->bands;z++)for(int i=0;i<6;i++)f->endweights[z*6+i]=wi[i][z];
    if(bw.fill)*bw.p++=(uint8_t)(bw.bits<<(8-bw.fill));return bw.p-f->output;
}
