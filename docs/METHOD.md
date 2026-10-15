# Method and qualified scope

This method changes the execution of an adaptive integer predictor; it does not define a new compression format. [The original derivation](../research/iac2027-vector-compression-kit/METHOD.md) and original source files are retained. This document gives the current interpretation after the stronger comparisons.

## Execution

For a block of at most eight adjacent samples in one band:

1. Draft the signs used by the predictor's weight updates with a cheap approximate calculation.
2. Compute candidate pre-sample weights using prefix sums of the drafted integer updates.
3. Recompute the exact integer prediction/sign for every candidate state and check every cumulative weight against the legal clipping interval.
4. Commit only if every check succeeds; otherwise replay the block with the exact scalar recurrence from the unchanged initial state.

If the initial candidate state is correct, the exact sign check gives the true update. The range check ensures that clipping does not invalidate the prefix sum. Induction then gives the correct next state and all predictions in an accepted block. Rejected blocks retain the original scalar behavior. Scene characteristics affect the acceptance rate and cost, not the conditional equivalence argument.

This ordinary induction argument, prefix computation and guarded speculation are not claimed as new general mathematics. Prior CCSDS dependency reduction, speculative updates, exact block filtering and update bypass are discussed in the [source list](../research/iac2027-vector-compression-kit/SOURCES.md). The particular implementation would require a demonstrated useful operating region to establish an engineering research contribution. The final audit did not establish that region for the intended spacecraft paper.

## Arithmetic and profile

The qualified full-pipeline profile is unsigned16, lossless, zero damping and exponent offsets, Ω=19, R=64, full prediction, P=3, initial adaptation parameter−1, final4/9, interval64, wide-neighbor or narrow-column local sums and sample-adaptive entropy coding. The original arithmetic contract is three to six active difference components, legal22-bit weights, bounded differences and 64-bit exact dot products. See the original derivation for its numerical bounds and compiler arithmetic-shift assumptions.

Blocks remain capped at eight. No near-lossless extension, general damping support, arbitrary vector-length speed scaling or hardware WCET guarantee is asserted. Near-lossless reconstruction changes later prediction contexts and requires a separate investigation.

## Comparisons and limits

Conventional spectral SIMD can preserve the same adaptive residual sequences, final weights and compressed size while using a different standard output interleaving. Exact byte identity with a selected BIL stream is not treated as a scientific requirement. Component SIMD, strong scalar implementations, calibrated fixed weights and independent contexts remain applicable where the actual workload permits them.

The latest RVV source includes ordinary component SIMD, compact spectral groups2/4/8, native-BIP spectral groups2/4/8/automaticVL and sequential/component BIP paths. Some feature gathering remains scalar; these are not proven best possible target implementations. Independent-context parallel SIMD is not implemented/timed. FixedΩ=12 is a host comparison, not integrated into the adaptive RVV Linux pilot.

Resident host timing excludes input-file reading, allocation, independent validation, header work and actual sensor/telemetry transfers. Reordering and data provenance are recorded per campaign. Trace-derived source-prefix availability is not measured DMA latency. Renode checks establish differential functional agreement for tested cases; its model time is not target performance.

The semantic verifier assumes correct execution. It is not a radiation fault detector and does not replace ECC, memory protection, checksums or redundant execution.

The preserved physical pilot is an experimental measurement entry point with incomplete comparison/integration work. It does not endorse starting a hardware campaign following the final NO-GO decision.
