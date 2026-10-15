/* Differential functional validation, not a timing benchmark. */
#include "revision_capture.c"
__attribute__((section(".results"))) volatile uint64_t status[8];
#define MAXN (37*5*128)
static uint16_t raw[MAXN],ring[2*37*128];
static int32_t scratch[10*37],band_scratch[7*37*8],predictions[37*8];
static uint8_t output[MAXN*6+16],gold_bil[MAXN*6+16],gold_bip[MAXN*6+16];
static uint32_t residual0[MAXN],residual1[MAXN];
static uint32_t rng=0xb782e941;
static uint32_t random32(void){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
static int equal(const void*a,const void*b,size_t n){const uint8_t*x=a,*y=b;for(size_t i=0;i<n;i++)if(x[i]!=y[i])return 0;return 1;}
int main(void){
    const int bands[]={1,2,3,4,6,8,9,17,120,128,4,7};
    const int methods[][2]={{1,1},{2,1},{7,2},{7,4},{7,8},{8,1},{10,1},{9,2},{9,4},{9,8},{9,0},{11,1},{12,1},{13,1}};
    for(int bi=0;bi<12;bi++)for(int local=0;local<=3;local+=3)for(int nu=4;nu<=9;nu+=5)for(int pat=0;pat<3;pat++){
        /* The two long cases reach both nu caps and exercise full/tail blocks.
         * Merely setting nu4/9 on short images would not test that difference.
         */
        int w=bi==10?17:bi==11?37:bi%3==0?2:bi%3==1?5:17;
        int h=bi==10?48:bi==11?40:bi%3==0?1:bi%3==1?2:5,z=bands[bi];size_t n=(size_t)w*h*z;
        if(bi>=10&&scaling((size_t)w*h-1,w,nu)!=nu-3){status[0]=0xbad00040;return 3;}
        for(size_t i=0;i<n;i++)raw[i]=pat==0?12345:pat==1?(i&1?65535:0):(uint16_t)random32();
        Frame f={0};f.width=w;f.height=h;f.bands=z;f.local=local;f.nu_max=nu;f.n=(size_t)w*h;f.bil=1;f.layout=1;f.raw=raw;f.ring=ring;f.scratch=scratch;f.band_scratch=band_scratch;f.predictions=predictions;
        int32_t weights0[128*6]={0},weights1[128*6]={0};Counts counts={0};
        f.output=gold_bil;f.endweights=weights0;capture_n=f.n;capture_values=residual0;size_t nb=run(&f,0,&counts);
        f.output=gold_bip;f.endweights=weights1;capture_values=residual1;size_t np=run(&f,11,&counts);
        if(np!=nb||!equal(residual0,residual1,n*4)||!equal(weights0,weights1,z*6*4)){status[0]=0xbad00011;status[2]++;return 1;}
        for(int k=0;k<14;k++){
            int variant=methods[k][0];f.output=output;f.group=methods[k][1];f.endweights=weights1;capture_values=residual1;
            size_t nn=run(&f,variant,&counts);int bip=variant==9||variant>=11;
            if(nn!=nb||!equal(output,bip?gold_bip:gold_bil,nb)||!equal(residual0,residual1,n*4)||!equal(weights0,weights1,z*6*4)){
                status[0]=0xbad00000+variant;status[2]++;status[3]=bi;status[4]=(uint64_t)local*100+(uint64_t)nu*10+pat;status[7]=k;return 2;
            }
            status[1]++;status[3]+=n;
        }
        status[4]++;
    }
    status[0]=0x600dcc53;return 0;
}
