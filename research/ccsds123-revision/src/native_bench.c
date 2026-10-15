/* Ratified RVV1.0 functional/performance pilot for the stated D16 profile.
 * Output bodies only. File I/O, allocation and verification are not timed.
 * Fixed-weight and independent-tile policies remain separate comparisons.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <sched.h>
#include "revision_harness.c"
int main(int argc,char**argv){
    if(argc!=10){fprintf(stderr,"Usage: %s input-u16le.raw width height bands local(0|3) nu(4|9) layout(BIP|BIL) repeats core\n",argv[0]);return 2;}
    int w=atoi(argv[2]),h=atoi(argv[3]),z=atoi(argv[4]),local=atoi(argv[5]),nu=atoi(argv[6]),layout=!strcmp(argv[7],"BIP"),repeats=atoi(argv[8]),core=atoi(argv[9]);
    if(w<2||w>65535||h<1||h>65535||z<1||z>128||(local!=0&&local!=3)||(nu!=4&&nu!=9)||(strcmp(argv[7],"BIP")&&strcmp(argv[7],"BIL"))||repeats<0||core<0||core>=CPU_SETSIZE)return 2;
    cpu_set_t affinity;CPU_ZERO(&affinity);CPU_SET(core,&affinity);if(sched_setaffinity(0,sizeof(affinity),&affinity)){perror("CPU affinity");return 2;}
    size_t n=(size_t)w*h*z;if(n>(SIZE_MAX-16)/6)return 2;
    uint16_t*raw=malloc(n*2);uint8_t*out=malloc(n*6+16),*bil=malloc(n*6+16),*bip=layout?malloc(n*6+16):0;
    if(!raw||!out||!bil||(layout&&!bip)){fprintf(stderr,"Insufficient memory for validation harness\n");return 2;}
    FILE*file=fopen(argv[1],"rb");if(!file){perror("Input");return 2;}
    if(fread(raw,2,n,file)!=n||fgetc(file)!=EOF){fprintf(stderr,"Input size mismatch\n");return 2;}fclose(file);
    void*c=make_context(raw,w,h,z,local,nu,layout);if(!c)return 2;
    int32_t weights0[128*6]={0},weights[128*6]={0};uint64_t counts[4]={0};
    size_t bytes=compute(c,0,1,0,weights0,bil,counts,0);
    if(layout){size_t nn=compute(c,11,1,0,weights,bip,counts,0);if(nn!=bytes||memcmp(weights,weights0,z*6*4))return 3;}
    int methods[][2]={{0,1},{1,1},{5,1},{8,1},{10,1},{2,1},{7,2},{7,4},{7,8},{9,2},{9,4},{9,8},{9,0},{11,1},{12,1},{13,1}};
    int total=layout?16:9;
    for(int k=0;k<total;k++){
        int v=methods[k][0],g=methods[k][1];size_t nn=compute(c,v,g,0,weights,out,counts,0);
        if(nn!=bytes||memcmp(out,v==9||v>=11?bip:bil,bytes)||memcmp(weights,weights0,z*6*4)){fprintf(stderr,"Validation mismatch method%d group%d\n",v,g);return 3;}
    }
    unsigned long vlenbytes;__asm__ volatile("csrr %0,vlenb":"=r"(vlenbytes));
    printf("{\"kind\":\"validation\",\"methods\":%d,\"body_bytes\":%zu,\"samples\":%zu,\"VLEN\":%lu,\"pass\":true,\"timing_scope\":\"resident compression body, excludes I/O, allocation, checks, header and telemetry\"}\n",total,bytes,n,vlenbytes*8);
    for(int trial=0;trial<repeats;trial++)for(int offset=0;offset<total;offset++){
        int k=(offset+trial)%total,v=methods[k][0],g=methods[k][1];uint64_t start=tick();size_t nn=compute(c,v,g,0,weights,out,counts,0);uint64_t end=tick();
        if(nn!=bytes||memcmp(out,v==9||v>=11?bip:bil,bytes)||memcmp(weights,weights0,z*6*4))return 3;
        printf("{\"kind\":\"timing\",\"trial\":%d,\"variant\":%d,\"group\":%d,\"samples\":%zu,\"ns_sample\":%.9f,\"start_ns\":%llu,\"end_ns\":%llu,\"accepted\":%llu,\"rejected\":%llu}\n",trial,v,g,n,(double)(end-start)/n,(unsigned long long)start,(unsigned long long)end,(unsigned long long)counts[0],(unsigned long long)counts[1]);fflush(stdout);
    }
    free_context(c);free(raw);free(out);free(bil);free(bip);return 0;
}
