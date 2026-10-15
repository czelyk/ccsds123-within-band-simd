#include <riscv_vector.h>
#define FN unused_rvv_scalar_wrapper
#include "portable.inc"
#undef FN
#define FN RVV_NAME
void FN(const Block*b,int32_t*w,Counts*counts){
#ifdef FROZEN
    (void)counts;
    for(size_t t=0;t<b->n;){
        size_t vl=__riscv_vsetvl_e32m1(b->n-t);
        vint64m2_t d=__riscv_vwadd_vx_i64m2(__riscv_vle32_v_i32m1(b->sigma+t,vl),0,vl);
        d=__riscv_vadd_vx_i64m2(__riscv_vsll_vx_i64m2(d,11,vl),4096,vl);
        for(int i=0;i<C;i++)d=__riscv_vadd_vv_i64m2(d,__riscv_vwmul_vx_i64m2(__riscv_vle32_v_i32m1(b->u[i]+t,vl),w[i],vl),vl);
        d=__riscv_vmin_vx_i64m2(__riscv_vmax_vx_i64m2(__riscv_vsra_vx_i64m2(d,12,vl),0,vl),131071,vl);
        __riscv_vse32_v_i32m1(b->output+t,__riscv_vncvt_x_x_w_i32m1(d,vl),vl);t+=vl;
    }
#else
    for(size_t t=0;t<b->n;){
        size_t request=b->n-t;
        if(request>8)request=8;
        size_t vl=__riscv_vsetvl_e32m1(request);
        vint32m1_t zero=__riscv_vmv_v_x_i32m1(0,vl);
        vint32m1_t sig=__riscv_vle32_v_i32m1(b->sigma+t,vl);
        vint32m1_t x2=__riscv_vsll_vx_i32m1(__riscv_vle32_v_i32m1(b->samples+t,vl),1,vl);
        vint32m1_t draft=zero;
        for(int i=0;i<C;i++){
            vint32m1_t u=__riscv_vle32_v_i32m1(b->u[i]+t,vl);
            draft=__riscv_vadd_vv_i32m1(draft,__riscv_vmul_vx_i32m1(u,w[i]>>8,vl),vl);
        }
        draft=__riscv_vadd_vv_i32m1(draft,__riscv_vsll_vx_i32m1(__riscv_vand_vx_i32m1(sig,1,vl),11,vl),vl);
        draft=__riscv_vadd_vx_i32m1(draft,4096,vl);
        draft=__riscv_vadd_vv_i32m1(__riscv_vsra_vx_i32m1(draft,12,vl),__riscv_vsra_vx_i32m1(sig,1,vl),vl);
        draft=__riscv_vmin_vx_i32m1(__riscv_vmax_vx_i32m1(draft,0,vl),131071,vl);
        vbool32_t positive=__riscv_vmsle_vv_i32m1_b32(draft,x2,vl);
        vint32m1_t signs=__riscv_vmerge_vxm_i32m1(__riscv_vmv_v_x_i32m1(-1,vl),1,positive,vl);
        vint32m1_t rr=__riscv_vle32_v_i32m1(b->rho+t,vl);
        vuint32m1_t sl=__riscv_vreinterpret_v_i32m1_u32m1(__riscv_vmax_vx_i32m1(__riscv_vneg_v_i32m1(rr,vl),0,vl));
        vuint32m1_t sr=__riscv_vreinterpret_v_i32m1_u32m1(__riscv_vmax_vx_i32m1(rr,0,vl));
        vbool32_t invalid=__riscv_vmclr_m_b32(vl);
        vint64m2_t d=__riscv_vwadd_vx_i64m2(sig,0,vl);
        d=__riscv_vadd_vx_i64m2(__riscv_vsll_vx_i64m2(d,19,vl),1<<20,vl);
        int32_t finalw[C];
        for(int i=0;i<C;i++){
            vint32m1_t u=__riscv_vle32_v_i32m1(b->u[i]+t,vl);
            vint32m1_t inc=__riscv_vmul_vv_i32m1(u,signs,vl);
            inc=__riscv_vsra_vv_i32m1(__riscv_vsll_vv_i32m1(inc,sl,vl),sr,vl);
            inc=__riscv_vsra_vx_i32m1(__riscv_vadd_vx_i32m1(inc,1,vl),1,vl);
            vint32m1_t prefix=inc;
            for(size_t shift=1;shift<vl;shift*=2){
                prefix=__riscv_vadd_vv_i32m1(prefix,__riscv_vslideup_vx_i32m1(zero,prefix,shift,vl),vl);
            }
            vint32m1_t end=__riscv_vadd_vx_i32m1(prefix,w[i],vl);
            invalid=__riscv_vmor_mm_b32(invalid,__riscv_vmslt_vx_i32m1_b32(end,WMIN,vl),vl);
            invalid=__riscv_vmor_mm_b32(invalid,__riscv_vmsgt_vx_i32m1_b32(end,WMAX,vl),vl);
            vint32m1_t states=__riscv_vsub_vv_i32m1(end,inc,vl);
            d=__riscv_vadd_vv_i64m2(d,__riscv_vwmul_vv_i64m2(states,u,vl),vl);
            finalw[i]=__riscv_vmv_x_s_i32m1_i32(__riscv_vslidedown_vx_i32m1(end,vl-1,vl));
        }
        d=__riscv_vsra_vx_i64m2(d,20,vl);
        d=__riscv_vmin_vx_i64m2(__riscv_vmax_vx_i64m2(d,0,vl),131071,vl);
        vint32m1_t exact=__riscv_vncvt_x_x_w_i32m1(d,vl);
        vbool32_t actual_sign=__riscv_vmsle_vv_i32m1_b32(exact,x2,vl);
        vbool32_t same=__riscv_vmxnor_mm_b32(positive,actual_sign,vl);
        if(__riscv_vcpop_m_b32(invalid,vl)==0 && __riscv_vcpop_m_b32(same,vl)==vl){
            __riscv_vse32_v_i32m1(b->output+t,exact,vl);
            for(int i=0;i<C;i++)w[i]=finalw[i];
            counts->accepted++;
        }else{
            for(size_t j=0;j<vl;j++)sample(b,t+j,w);
            counts->rejected++;
        }
        t+=vl;
    }
#endif
}
