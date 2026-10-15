/* Conventional SIMD over the predictor components of a sequential sample.
 * Two ordinary LMUL choices are retained; hardware must decide their cost.
 * Stated profile only: D16/Omega19, lossless, zero damping/offsets.
 */
static inline int component_update(int32_t*u,int sigma,int actual2,int32_t*w,int c,int r,int lmul){
    int64_t dot=0;
    if(lmul==2){
        size_t vl=__riscv_vsetvl_e32m2(c);
        vint32m2_t uv=__riscv_vle32_v_i32m2(u,vl),wv=__riscv_vle32_v_i32m2(w,vl);
        vint64m4_t products=__riscv_vwmul_vv_i64m4(uv,wv,vl);
        vint64m1_t sum=__riscv_vredsum_vs_i64m4_i64m1(products,__riscv_vmv_v_x_i64m1(0,1),vl);
        dot=__riscv_vmv_x_s_i64m1_i64(sum);
    }else for(int first=0;first<c;){
        size_t vl=__riscv_vsetvl_e32m1(c-first);
        vint64m2_t products=__riscv_vwmul_vv_i64m2(__riscv_vle32_v_i32m1(u+first,vl),__riscv_vle32_v_i32m1(w+first,vl),vl);
        dot+=__riscv_vmv_x_s_i64m1_i64(__riscv_vredsum_vs_i64m2_i64m1(products,__riscv_vmv_v_x_i64m1(0,1),vl));
        first+=vl;
    }
    int p=clamp(((int64_t)sigma*524288+1048576+dot)>>20,0,131071),s=actual2>=p?1:-1;
    if(lmul==2){
        size_t vl=__riscv_vsetvl_e32m2(c);
        vint32m2_t a=__riscv_vmul_vx_i32m2(__riscv_vle32_v_i32m2(u,vl),s,vl);
        a=r>=0?__riscv_vsra_vx_i32m2(a,r,vl):__riscv_vsll_vx_i32m2(a,-r,vl);
        a=__riscv_vsra_vx_i32m2(__riscv_vadd_vx_i32m2(a,1,vl),1,vl);
        a=__riscv_vadd_vv_i32m2(a,__riscv_vle32_v_i32m2(w,vl),vl);
        __riscv_vse32_v_i32m2(w,__riscv_vmin_vx_i32m2(__riscv_vmax_vx_i32m2(a,-2097152,vl),2097151,vl),vl);
    }else for(int first=0;first<c;){
        size_t vl=__riscv_vsetvl_e32m1(c-first);
        vint32m1_t a=__riscv_vmul_vx_i32m1(__riscv_vle32_v_i32m1(u+first,vl),s,vl);
        a=r>=0?__riscv_vsra_vx_i32m1(a,r,vl):__riscv_vsll_vx_i32m1(a,-r,vl);
        a=__riscv_vsra_vx_i32m1(__riscv_vadd_vx_i32m1(a,1,vl),1,vl);
        a=__riscv_vadd_vv_i32m1(a,__riscv_vle32_v_i32m1(w+first,vl),vl);
        __riscv_vse32_v_i32m1(w+first,__riscv_vmin_vx_i32m1(__riscv_vmax_vx_i32m1(a,-2097152,vl),2097151,vl),vl);
        first+=vl;
    }
    return p;
}
static void component_row(Frame*f,int z,int y,Writer*bw,int32_t*w,Entropy*e,int lmul){
    int c=3+(z<3?z:3);
    for(int x=!y;x<f->width;x++){
        int32_t u[6]={0};int sigma=local_values(f,z,x,y,u);
        size_t t=(size_t)y*f->width+x;
        int p=component_update(u,sigma,2*f->cur[z][x],w,c,scaling(t,f->width,f->nu_max),lmul);
        encode(bw,e,mapped(f->cur[z][x],p),t);
    }
}
