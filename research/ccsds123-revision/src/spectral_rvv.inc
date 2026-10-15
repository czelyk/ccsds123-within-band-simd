/* Established spectral SIMD with natural short VLs, not a contribution claim.
 * Features are scalar-gathered; no claim of globally optimal RVV code.
 */
static inline __attribute__((always_inline)) void spectral_step_impl(int32_t*features,int stride,int32_t*actual,int32_t wi[6][128],int base,int r,size_t vl,int32_t*pp,int components){
    vint64m2_t d=__riscv_vwadd_vx_i64m2(__riscv_vle32_v_i32m1(features+6*stride,vl),0,vl);
    d=__riscv_vadd_vx_i64m2(__riscv_vsll_vx_i64m2(d,19,vl),1048576,vl);
    for(int i=0;i<components;i++)d=__riscv_vadd_vv_i64m2(d,__riscv_vwmul_vv_i64m2(__riscv_vle32_v_i32m1(features+i*stride,vl),__riscv_vle32_v_i32m1(wi[i]+base,vl),vl),vl);
    d=__riscv_vmin_vx_i64m2(__riscv_vmax_vx_i64m2(__riscv_vsra_vx_i64m2(d,20,vl),0,vl),131071,vl);
    vint32m1_t p=__riscv_vncvt_x_x_w_i32m1(d,vl);
    __riscv_vse32_v_i32m1(pp,p,vl);
    vbool32_t positive=__riscv_vmsle_vv_i32m1_b32(p,__riscv_vle32_v_i32m1(actual,vl),vl);
    vint32m1_t signs=__riscv_vmerge_vxm_i32m1(__riscv_vmv_v_x_i32m1(-1,vl),1,positive,vl);
    for(int i=0;i<components;i++){
        vint32m1_t a=__riscv_vmul_vv_i32m1(__riscv_vle32_v_i32m1(features+i*stride,vl),signs,vl);
        a=r>=0?__riscv_vsra_vx_i32m1(a,r,vl):__riscv_vsll_vx_i32m1(a,-r,vl);
        a=__riscv_vsra_vx_i32m1(__riscv_vadd_vx_i32m1(a,1,vl),1,vl);
        a=__riscv_vadd_vv_i32m1(a,__riscv_vle32_v_i32m1(wi[i]+base,vl),vl);
        __riscv_vse32_v_i32m1(wi[i]+base,__riscv_vmin_vx_i32m1(__riscv_vmax_vx_i32m1(a,-2097152,vl),2097151,vl),vl);
    }
}
static void spectral_step(int32_t*features,int stride,int32_t*actual,int32_t wi[6][128],int base,int r,size_t vl,int32_t*pp){
    int last=base+(int)vl-1,components=3+(last<3?last:3);
    switch(components){
      case 3:spectral_step_impl(features,stride,actual,wi,base,r,vl,pp,3);break;
      case 4:spectral_step_impl(features,stride,actual,wi,base,r,vl,pp,4);break;
      case 5:spectral_step_impl(features,stride,actual,wi,base,r,vl,pp,5);break;
      default:spectral_step_impl(features,stride,actual,wi,base,r,vl,pp,6);break;
    }
}
static void band_parallel_compact(Frame*f,Writer*writers,Entropy*states){
    int32_t wi[6][128]={{0}};
    for(int z=0;z<f->bands;z++)for(int i=3;i<3+(z<3?z:3);i++)wi[i][z]=i==3?458752:wi[i-1][z]/8;
    for(int y=0;y<f->height;y++)for(int base=0;base<f->bands;){
        int request=f->bands-base;if(request>f->group)request=f->group;if(request>8)request=8;
        size_t vl=__riscv_vsetvl_e32m1(request);prepare_group(f,y,base,vl);
        for(int x=!y;x<f->width;x++){
            int32_t features[7][8],actual[8],pp[8];
            for(size_t lane=0;lane<vl;lane++){
                int32_t u[6]={0};int z=base+lane;
                features[6][lane]=local_values(f,z,x,y,u);actual[lane]=2*f->cur[z][x];
                for(int i=0;i<6;i++)features[i][lane]=u[i];
            }
            spectral_step(&features[0][0],8,actual,wi,base,scaling((size_t)y*f->width+x,f->width,f->nu_max),vl,pp);
            for(size_t lane=0;lane<vl;lane++)f->predictions[lane*f->width+x]=pp[lane];
        }
        for(size_t lane=0;lane<vl;lane++){
            int z=base+lane;Writer*dest=f->bil?writers:writers+z;
            if(f->bil&&!y)encode(dest,states+z,mapped(f->cur[z][0],z?2*f->cur[z-1][0]:65536),0);
            for(int x=!y;x<f->width;x++)encode(dest,states+z,mapped(f->cur[z][x],f->predictions[lane*f->width+x]),(size_t)y*f->width+x);
        }
        base+=vl;
    }
    if(f->endweights)for(int z=0;z<f->bands;z++)for(int i=0;i<6;i++)f->endweights[z*6+i]=wi[i][z];
}
static void band_parallel(Frame*f,Writer*w,Entropy*e){band_parallel_compact(f,w,e);}
