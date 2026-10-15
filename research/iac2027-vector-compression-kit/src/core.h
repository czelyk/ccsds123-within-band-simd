#ifndef CORE_H
#define CORE_H
#include <stdint.h>
#include <stddef.h>
typedef struct {
    const int32_t *u[6], *sigma, *samples, *rho;
    int32_t *output;
    size_t n;
} Block;
typedef struct { uint64_t accepted, rejected; } Counts;
typedef void (*Kernel)(const Block*,int32_t*,Counts*);
#define DECLARE(N) void scalar##N(const Block*,int32_t*,Counts*); void avx##N(const Block*,int32_t*,Counts*); void rvv##N(const Block*,int32_t*,Counts*)
DECLARE(3); DECLARE(4); DECLARE(5); DECLARE(6);
void frozen3(const Block*,int32_t*,Counts*);void frozen4(const Block*,int32_t*,Counts*);void frozen5(const Block*,int32_t*,Counts*);void frozen6(const Block*,int32_t*,Counts*);
#endif
