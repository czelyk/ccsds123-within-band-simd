/* Conventional inter-band SIMD; all bands must be available. */
static void band_parallel(Frame*f,Writer*writers,Entropy*states){
    int32_t initial[6][8]={{0}};
    for(int z=0;z<f->bands;z++){int c=3+(z<3?z:3);int32_t w[6];init(w,c);for(int i=0;i<c;i++)initial[i][z]=w[i];}
    for(int y=0;y<f->height;y++){
      prepare_rows(f,y,-1);
      for(int zbase=0;zbase<f->bands;){
        size_t vl=__riscv_vsetvl_e32m1(f->bands-zbase);
#define INIT_W(I) vint32m1_t w##I=__riscv_vle32_v_i32m1(initial[I]+zbase,vl)
        INIT_W(0);INIT_W(1);INIT_W(2);INIT_W(3);INIT_W(4);INIT_W(5);
#undef INIT_W
            int x0=!y;
            for(int x=x0;x<f->width;x++)for(size_t lane=0;lane<vl;lane++){
                int u[6]={0},z=zbase+lane,sigma=local_values(f,z,x,y,u);
                for(int i=0;i<6;i++)f->band_scratch[(7*(size_t)x+i)*8+lane]=u[i];
                f->band_scratch[(7*(size_t)x+6)*8+lane]=sigma;
            }
            for(int x=x0;x<f->width;x++){
                size_t t=(size_t)y*f->width+x;int r=scaling(t,f->width,f->nu_max);
                vint64m2_t d=__riscv_vwadd_vx_i64m2(__riscv_vle32_v_i32m1(f->band_scratch+(7*(size_t)x+6)*8,vl),0,vl);
                d=__riscv_vadd_vx_i64m2(__riscv_vsll_vx_i64m2(d,19,vl),1048576,vl);
#define DOT(I) vint32m1_t u##I=__riscv_vle32_v_i32m1(f->band_scratch+(7*(size_t)x+I)*8,vl);d=__riscv_vadd_vv_i64m2(d,__riscv_vwmul_vv_i64m2(u##I,w##I,vl),vl)
                DOT(0);DOT(1);DOT(2);DOT(3);DOT(4);DOT(5);
#undef DOT
                d=__riscv_vmin_vx_i64m2(__riscv_vmax_vx_i64m2(__riscv_vsra_vx_i64m2(d,20,vl),0,vl),131071,vl);
                vint32m1_t p=__riscv_vncvt_x_x_w_i32m1(d,vl);int32_t pp[8],actual[8];__riscv_vse32_v_i32m1(pp,p,vl);
                for(size_t lane=0;lane<vl;lane++){int z=zbase+lane;f->predictions[z*f->width+x]=pp[lane];actual[lane]=2*f->cur[z][x];}
                vbool32_t positive=__riscv_vmsle_vv_i32m1_b32(p,__riscv_vle32_v_i32m1(actual,vl),vl);
                vint32m1_t signs=__riscv_vmerge_vxm_i32m1(__riscv_vmv_v_x_i32m1(-1,vl),1,positive,vl);
#define UPDATE(I) {vint32m1_t a=__riscv_vmul_vv_i32m1(u##I,signs,vl);if(r>=0)a=__riscv_vsra_vx_i32m1(a,r,vl);else a=__riscv_vsll_vx_i32m1(a,-r,vl);a=__riscv_vsra_vx_i32m1(__riscv_vadd_vx_i32m1(a,1,vl),1,vl);w##I=__riscv_vmin_vx_i32m1(__riscv_vmax_vx_i32m1(__riscv_vadd_vv_i32m1(w##I,a,vl),-2097152,vl),2097151,vl);}
                UPDATE(0);UPDATE(1);UPDATE(2);UPDATE(3);UPDATE(4);UPDATE(5);
#undef UPDATE
            }
            for(size_t lane=0;lane<vl;lane++){
                int z=zbase+lane;Writer*dest=f->bil?writers:writers+z;
                if(f->bil&&!y)encode(dest,states+z,mapped(f->cur[z][0],z?2*f->cur[z-1][0]:65536),0);
                for(int x=x0;x<f->width;x++){size_t t=(size_t)y*f->width+x;encode(dest,states+z,mapped(f->cur[z][x],f->predictions[z*f->width+x]),t);}
                if(f->bil&&!y&&!z)f->first_row_after_received=f->received_rows;
            }
#define SAVE_W(I) __riscv_vse32_v_i32m1(initial[I]+zbase,w##I,vl)
            SAVE_W(0);SAVE_W(1);SAVE_W(2);SAVE_W(3);SAVE_W(4);SAVE_W(5);
#undef SAVE_W
        zbase+=vl;
      }
    }
}
