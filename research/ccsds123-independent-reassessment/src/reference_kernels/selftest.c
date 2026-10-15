#include "core.h"
#ifndef BARE
#include <stdio.h>
#endif
#include "reference_cases.h"
volatile uint64_t status[8] __attribute__((section(".results")));
static int32_t ux[6][67], sx[67], ax[67], rx[67], oa[67], ob[67], wa[6], wb[6];
static uint32_t rng=0x4aa9f321;
static uint32_t random32(void){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
static Kernel serials[4]={scalar3,scalar4,scalar5,scalar6};
#ifdef BARE
static Kernel parallel[4]={rvv3,rvv4,rvv5,rvv6};
#else
static Kernel parallel[4]={avx3,avx4,avx5,avx6};
#endif
static void verify(const Block*b,int c,const int32_t*initial,const int32_t*gold){
    Counts counts={0};Block first=*b,second=*b;first.output=oa;second.output=ob;
    for(int i=0;i<c;i++)wa[i]=wb[i]=initial[i];
    serials[c-3](&first,wa,&counts);
    parallel[c-3](&second,wb,&counts);
    for(size_t i=0;i<b->n;i++){
        status[1]++;
        if(oa[i]!=ob[i]||(gold&&oa[i]!=gold[i]))status[2]++;
    }
    for(int i=0;i<c;i++)if(wa[i]!=wb[i])status[2]++;
    status[3]+=counts.accepted;status[4]+=counts.rejected;
}
int main(void){
    for(int i=0;i<8;i++)status[i]=0;
    /* Independent NTNU expected values. Split into chunks to also test
     * state continuity and tails, not just a single whole-array call. */
    for(int r=0;r<2;r++){
        int c=r?3:6;int32_t current[6];
        for(int i=0;i<c;i++)current[i]=r?ref1_init[i]:ref0_init[i];
        const int32_t *ref_u=r?ref1_u[0]:ref0_u[0];
        for(size_t t=0;t<513;){
            size_t n=(t%29)+1;if(t+n>513)n=513-t;
            Block b={0};b.n=n;
            for(int i=0;i<c;i++)b.u[i]=ref_u+i*513+t;
            b.sigma=(r?ref1_sigma:ref0_sigma)+t;b.samples=(r?ref1_samples:ref0_samples)+t;
            b.rho=(r?ref1_rho:ref0_rho)+t;
            verify(&b,c,current,(r?ref1_gold:ref0_gold)+t);
            for(int i=0;i<c;i++)current[i]=wa[i];
            t+=n;
        }
    }
    /* Low-level arithmetic profile stress. Some combinations need not
     * correspond to a physical image. They test the stated kernel contract. */
    for(int c=3;c<=6;c++){
        for(int trial=0;trial<500;trial++){
            size_t n=(size_t)(trial%68);Block b={0};b.n=n;
            int32_t initial[6];
            for(int i=0;i<c;i++){
                b.u[i]=ux[i];initial[i]=(int32_t)(random32()%4194304)-2097152;
                if(trial%3==0)initial[i]=2097151;
                if(trial%3==1)initial[i]=-2097152;
            }
            for(size_t t=0;t<n;t++){
                sx[t]=(int32_t)(random32()%262141);ax[t]=(int32_t)(random32()&65535);
                rx[t]=(int32_t)(random32()%16)-9;
                for(int i=0;i<c;i++)ux[i][t]=(int32_t)(random32()%524281)-262140;
            }
            b.sigma=sx;b.samples=ax;b.rho=rx;verify(&b,c,initial,0);
        }
    }
    status[0]=status[2]?0xbadcc530:0x600dcc53;
#ifndef BARE
    printf("comparisons=%llu mismatches=%llu accepted=%llu rejected=%llu magic=%llx\n",
        (unsigned long long)status[1],(unsigned long long)status[2],(unsigned long long)status[3],(unsigned long long)status[4],(unsigned long long)status[0]);
#endif
    return status[2]?1:0;
}
