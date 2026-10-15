/* Included with compile-time C and FN. Narrow, stated experimental profile:
 * unsigned16, Omega19,R64,zero exponent offsets,lossless,zero damping.
 * This is a software equivalence check, not a hardware-fault detector. */
#include "core.h"
#ifndef OMEGA
#define OMEGA 19
#endif
#define WMIN (-(1<<21))
#define WMAX ((1<<21)-1)
static inline int32_t clamp64(int64_t x,int32_t lo,int32_t hi){return x<lo?lo:x>hi?hi:(int32_t)x;}
static inline int32_t step(int32_t u,int32_t s,int r){
    int64_t x=(int64_t)u*s;
    x=r>=0?x>>r:x*((int64_t)1<<-r);
    return (int32_t)((x+1)>>1);
}
static inline void sample(const Block*b,size_t t,int32_t*w){
    int64_t d=(int64_t)b->sigma[t]*(1<<19)+(1<<20);
    for(int i=0;i<C;i++)d+=(int64_t)b->u[i][t]*w[i];
    int32_t p=clamp64(d>>20,0,131071);
    int s=2*b->samples[t]>=p?1:-1;
    for(int i=0;i<C;i++)w[i]=clamp64((int64_t)w[i]+step(b->u[i][t],s,b->rho[t]),WMIN,WMAX);
    b->output[t]=p;
}
void FN(const Block*b,int32_t*w,Counts*counts){
    (void)counts;
    for(size_t t=0;t<b->n;t++)sample(b,t,w);
}
