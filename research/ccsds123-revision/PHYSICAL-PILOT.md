> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# Physical pilot after revision

This is a prototype measurement entry point, not evidence that the scientific workload gate has passed. The existing method's scope remains lossless unsigned 16-bit, Ω=19/R64/P3, zero damping and zero exponent offsets. Do not use it unchanged for the raw D8/D10 corpus or LandIS near-lossless settings.

Use a 64-bit Linux target with ratified RVV 1.0, the required 64-bit widening/reduction operations, vector state enabled by the OS, and Clang 18 or another verified compatible compiler. The supplied build also enables Zba/Zbb; verify the complete recorded ISA against the target. No particular board purchase is prescribed.

`build_revision.py` first materializes the unchanged proposal plus conventional RVV baseline harness. The functional test has separate capture instrumentation. `native_bench.c` includes the uninstrumented harness. Source and fixture hashes must accompany results.

The generated harness is included. On a compatible target, build the Linux pilot with:

```text
python3 build_linux.py
```

To regenerate the harness and bare-metal validation, use `build_revision.py` with `LLD` pointing to a RISC-V-capable LLVM linker. A prepared Linux cross-build is supplied in `build/revision-pilot-rvv`; its manifest records the toolchain and that it has not run on a physical board. To reproduce a cross-build, pass the real `--sysroot`, `--gcc-dir` and `--lld` paths to `build_linux.py`.

The executable accepts a complete unsigned 16-bit little-endian image in BIP or BIL storage:

```text
./build/revision-pilot-rvv image-u16le-bip.raw WIDTH HEIGHT BANDS 3 9 BIP 0 CORE
```

Zero repetitions performs output/state validation only. Stop on any mismatch or illegal instruction. After validation, use a bounded repeated run, for example 25 trials, with the same selected core and controlled or logged frequency/temperature. The number 25 is a measurement choice, not a research acceptance criterion.

```text
./build/revision-pilot-rvv image-u16le-bip.raw WIDTH HEIGHT BANDS 3 9 BIP 25 CORE
```

The driver rotates method order and validates all outputs before and after timing. Methods include fused/staged/eager scalar, component SIMD at LMUL 1/2, the unchanged within-band method, compact spectral groups 2/4/8, native-BIP spectral groups 2/4/8/automatic VL, and native-BIP scalar/component paths. BIP output is allowed to differ from BIL output while preserving the same per-band residual sequence and byte count. `group=0` applies only to native BIP automatic vector length. Compact BIL is currently capped at 8 lanes; do not call that a globally optimized wide-vector baseline.

The driver measures resident compression bodies, including feature generation/adaptation/entropy packing. File reading, allocation, validation, headers and telemetry/DMA are excluded. It keeps large reference/output reservations for checking; those allocations are not flight working-memory requirements. The compact RVV helpers are functional baseline implementations, not yet architecture-tuned best code. The physical baseline tuning effort must be comparable to the proposal's effort.

Before making a paper decision, extend the experiment to the actual source/sink and approved payload profile, retain calibrated fixed-weight and independent-context alternatives, and measure cycles/time, working RAM/stack/code, output readiness, fallback latency distribution and energy per completed image. Record the power measurement boundary and synchronization uncertainty. Timing timestamps alone are not energy measurements.

The current spectral RVV helper gathers features with scalar code. A credible target comparison must also assess vector feature extraction or justify its cost on the selected target. The Ω=12 fixed-weight follow-up is a host implementation, not yet integrated in this adaptive Linux pilot. These are explicit remaining comparison tasks if a matching application is established; the supplied binary is not the completed paper experiment.

Independent stripe-reset size results in the host pilot include the CCSDS header of each stripe, but not a mission-specific container/index/packet overhead. Parallel tile SIMD is not implemented or timed by those results. Include its implementation and arrival/buffering costs if the workload permits independent contexts; do not exclude it because the output differs.

A documented operational budget and a representative profile-matched workload remain prerequisites for claiming spacecraft benefit. The prepared executable establishes a route to a fairer measurement; it does not establish a GO decision or IAC eligibility.
