#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
void* make_context(uint16_t*,int,int,int,int,int,int);
uint64_t compute(void*,int,int,int,int32_t*,uint8_t*,uint64_t*,uint64_t*);
uint64_t capture_compute(void*,int,int,int32_t*,uint8_t*,uint64_t*,uint32_t*);
void free_context(void*);
static uint32_t seed=0xb782e941;
static uint32_t random32(void){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;}
int main(void){
    const int widths[]={2,5,17},heights[]={1,2,5},bands[]={1,2,3,4,5,6,7,8,9,17};
    uint64_t cases=0,checks=0,samples=0;
    for(int a=0;a<3;a++)for(int b=0;b<3;b++)for(int c=0;c<10;c++)for(int local=0;local<=3;local+=3)for(int nu=4;nu<=9;nu+=5)for(int pat=0;pat<3;pat++){
        int w=widths[a],h=heights[b],z=bands[c];size_t n=(size_t)w*h*z;
        uint16_t *raw=calloc(n,2);uint8_t *out=malloc(n*6+16),*gold=malloc(n*6+16);
        uint32_t *r0=malloc(n*4),*r1=malloc(n*4);int32_t w0[128*6]={0},w1[128*6]={0};uint64_t counts[4]={0};
        for(size_t t=0;t<n;t++)raw[t]=pat==0?12345:pat==1?(t&1?65535:0):(uint16_t)random32();
        void*ctx=make_context(raw,w,h,z,local,nu,1);if(!ctx)return 2;
        uint64_t bytes=capture_compute(ctx,0,1,w0,gold,counts,r0);
        const int methods[][2]={{2,1},{7,2},{7,4},{7,8},{8,1}};
        for(int k=0;k<5;k++){
            uint64_t nn=compute(ctx,methods[k][0],methods[k][1],0,w1,out,counts,0);
            if(nn!=bytes||memcmp(out,gold,bytes)){fprintf(stderr,"BIL mismatch case%llu v%d g%d\n",(unsigned long long)cases,methods[k][0],methods[k][1]);return 3;}
            checks++;
        }
        for(int g=2;g<=8;g*=2){
            uint64_t nn=capture_compute(ctx,9,g,w1,out,counts,r1);
            if(nn!=bytes||memcmp(r0,r1,n*4)||memcmp(w0,w1,(size_t)z*6*4)){fprintf(stderr,"BIP residual/state mismatch case%llu g%d\n",(unsigned long long)cases,g);return 4;}
            checks++;samples+=n;
        }
        cases++;free_context(ctx);free(raw);free(out);free(gold);free(r0);free(r1);
    }
    printf("{\"cases\":%llu,\"method_checks\":%llu,\"mapped_residual_comparisons\":%llu,\"mismatches\":0}\n",(unsigned long long)cases,(unsigned long long)checks,(unsigned long long)samples);
    return 0;
}
