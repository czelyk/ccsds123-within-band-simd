> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# Physical measurement protocol

Read `FAIR_REVIEW.md` before committing resources. A small physical falsification experiment remains reasonable; commitment to this as a strong IAC paper is NO-GO on current evidence. Resolve the mission requirement and stronger latency-baseline gaps before a major hardware campaign. No physical measurements are included in this kit. IAC eligibility and final paper suitability remain separate decisions described in the reviews.

## Equipment and first execution

Use a board with ratified RVV 1.0, 64-bit vector integer/widening operations, and an operating system that enables vector state. The documented BPI-F3/SpacemiT K1 is a practical initial platform. A PIC64-HPSC engineering-model platform would give stronger space-hardware evidence; results from another processor cannot be substituted for its measurements.

On the board, build and validate with a suitable Clang toolchain:

```sh
CC=clang-18 python3 src/build.py rvv-native
python3 src/run_suite.py --repeats 0 --out results-validation
```

Stop if any comparison fails. An illegal-instruction error requires checking the board's ISA and OS support; it is not a performance result. A static RISC-V Linux executable was also successfully cross-compiled with Clang18 and a glibc2.39 sysroot. It has not run on a physical board. To reproduce the cross-build, supply your toolchain's paths:

```sh
CC=clang-18 python3 src/build.py rvv-linux-cross --sysroot /absolute/path/to/riscv64-linux-gnu --gcc-dir /absolute/path/to/gcc-cross/riscv64-linux-gnu/13 --lld /absolute/path/to/ld.lld
```

## Measurements

1. Record the board revision, processor, vector register size, OS/kernel, compiler, source/fixture hashes, clock policy, cooling, ambient temperature and available CPU affinity. Keep settings consistent. Record thermal throttling and background activity; do not silently remove poor trials.
2. Run complete-compressor timings on one consistent core. The example core number is only an example; use an available application core on the selected board.

```sh
python3 src/run_suite.py --core 2 --repeats 100 --out results-timing
```

3. Compare method2 with the fastest applicable same-configuration baseline: fused scalar0, staged scalar1, eager-sign scalar5, and band SIMD3 when its input batching is allowed. Method4 uses a different, fixed-weight configuration and must also be reported with compressed size and calibration assumptions. Never treat it as bit-identical to the adaptive configuration.
4. Report whole-compressor time, throughput, per-row completion latency under an explicit input schedule, acceptance/fallback counts, code size, working buffers and measured stack. Separate warm-cache results from larger-working-set and competing-task tests. The supplied repeated benchmark is mainly a warm replay experiment. It does not measure a sensor interface or include file loading in compression time.
5. Include constant, checkerboard and noise cases and the larger crop. Expand to independently acquired raw payload/spacecraft images, including dark, saturated, noisy and abrupt-transition scenes. Three processed airborne scenes and their spectral subsets are not a representative mission corpus.
6. Validate the row source/sink adapter for the intended interface. In BIL, the supplied within-band path consumes the current band row; the supplied band-SIMD path needs a complete spectral line. Measure this trade-off under a credible payload arrival schedule. Do not advertise the scalar/fixed paths' same one-row availability as an exclusive invention.

## Energy

Measure the board input or the relevant processor rail with a calibrated instrument. State which boundary was measured. Board energy is not CPU-only energy. Use equal completed input work, report idle power separately, and retain uncertainty and synchronization error.

For long, individually identifiable power windows, an optional final argument selects one timed variant. All applicable variants are still checked before timing. Adjust repetition count until intervals are long enough for the instrument:

```sh
./src/fullbench src/frame_pavia_bil_nu9_NARROW_COLUMN_ORIENTED.bin 10000 2 > power-method2.jsonl
```

Timing records contain monotonic start/end timestamps. Synchronize the instrument to that clock or use a measured hardware trigger; do not assume unrelated devices share a clock. A power log with `time_s,power_w` columns can be integrated with:

```sh
python3 src/integrate_energy.py measured-power.csv --start START_TIME --end END_TIME
```

No example physical values are supplied. Compare joules per input sample, total energy per completed frame and compressed output size. Long windows should also reveal frequency/temperature effects. A speedup does not by itself establish energy savings.

## Predefined paper decision

These are engineering research thresholds, not IAC selection criteria:

- Correctness: no unresolved mismatch, including on new raw data and the actual source/sink adapter.
- Practical benefit: target at least 1.20× geometric-mean speedup over the best applicable bit-exact baseline on an independently selected representative corpus, plus a useful latency or energy result under a concrete system requirement. Include all scenes and uncertainty, not just a favorable mean.
- Scope: no unexplained deadline failures, unacceptable memory/stack use or unreported data-dependent slowdowns. If an operational mode needs a scalar selection policy, evaluate that policy separately and acknowledge its established nature.
- Alternatives: report when fixed weights or band parallelism is the better choice. If an established alternative meets the same mission requirements more effectively and the new method adds no useful trade-off, the acceptance-focused paper is NO-GO.
- Stop the current paper if the apparent advantage disappears on hardware, is mainly measurement noise, requires cherry-picked data, or depends on a contrived input constraint. Do not broaden claims to compensate.

Before submission, obtain the IAF clarification on the documented AI assistance, update the closest-prior review, and have the human authors independently own the experimental design, interpretation and scientific claims. Rewriting alone does not establish policy compliance.
