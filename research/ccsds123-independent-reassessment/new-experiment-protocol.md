> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# Bounded independent reassessment experiments

Frozen before inspecting new comparator timings, 15 October 2026.

Question: does a conventional SIMD implementation across the three-to-six predictor components, while keeping samples sequential, remove the proposal's useful single-band execution point? This is an ordinary baseline, not a new claimed algorithm.

Retain the four previously selected HYPSO captures and both supported local sums. Test the full 956x684x120 images, native BIP layout, main nu_max=9, variants fused scalar0, unchanged within-band2, compact band7 groups4/8, and component SIMD8. Three rotated paired trials per case, no result-based exclusions. Confirm Finnmark narrow-column nu_max=4 as a previously selected sensitivity case. Confirm Finnmark native BIL replay at nu_max=9 with groups2/4/8 and five paired trials. BIL replay is a surrogate arrival order, not the actual HYPSO source format.

Before timing, all first8 full-width/full-band prefixes must match the independent-reference hashes already recorded; all new full-image outputs must match the scalar output and historical full-image hashes byte-for-byte. Save every timing trial before computing summaries, including scheduler/frequency outliers. Native code uses Clang18 O3 march=native shared-library build; do not merge timing samples with the historical MCJIT or GCC campaigns. Pin the same CPU core; report that frequency is not controlled.

Timing includes native-layout gathering into the two-line ring, local features, prediction, adaptation, entropy encoding and bit packing. Dataset I/O, context allocation, Python output comparisons, header construction, output file/telemetry transfer and physical DMA/interference are excluded. No measured energy or embedded RVV speed claims are allowed.

Collect fresh full diagnostic timestamp arrays in compressed local files for preselected Finnmark BIL methods0/2/7g2/7g4/7g8/8, separately from performance trials. Row-end timestamps are upper bounds on byte availability, not within-row packet measurements. Raw-data and code checksums must be recorded. Existing code and old evidence remain untouched.

If component SIMD wins, retain that negative finding and reconsider whether speculative within-band processing earns its complexity. If it loses, conclude only that this tested baseline does not eliminate the host advantage; do not extrapolate to native RVV reductions or globally optimal code. A limited host comparison cannot establish or refute all possible component SIMD implementations.

The final judgment can be GO, REVISE or NO-GO. Do not manufacture a new mission deadline, choose a convenient band count, or rebrand ordinary queueing/benchmark results as an original framework.

## Outcome-independent second baseline amendment

Direct code inspection showed that the historical native-BIP-input tests force BIL output for every method. No mission requirement justifies that compressed-byte-order constraint. Add conventional native-BIP-input/BIP-output band SIMD (variant9, groups4/8), preserving all per-band predictor and entropy sequences, the exact pixels, and the compressed bit count, while allowing the standard-compliant compressed byte ordering to differ. This is established spectral parallelism, not a new claimed contribution.

Validate the first8 rows of Finnmark for both local sums at nu_max9, and narrow-column nu_max4, against the unmodified NTNU model with BI depth=120. For all eight full main cases, independently instrument scalar BIL and native BIP to capture EVERY mapped residual into a common band-major array and compare all values plus final weights, byte count and the scalar historical hash. Use a separate instrumented shared library for this correctness check; time only the uninstrumented library. This full-cube comparison is against the specialized C scalar, not an independent full-cube Python reference. Capture-buffer writes are excluded from performance timing.

Run three rotated paired native-BIP trials of variants2,7g8,9g4,9g8 on the unchanged four full captures and both local sums. Repeat the previously selected Finnmark narrow nu_max4 sensitivity. Retain all results even if the established BIP ordering dominates or loses. Save the first512 diagnostic BIP group events on Finnmark separately; they cover first-byte-quantum availability, not full hardware input-to-output latency. Do not run timing jobs concurrently.
