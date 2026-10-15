> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# Method, correctness and limits

This is an execution transformation of a stated CCSDS 123 lossless profile. It does not define a new codec, fault detector, general scan algorithm or mathematical theorem.

For sample j and weight component i, let P(w,U,σ) be the exact double-resolution prediction, including clipping. Define b(j)=+1 when 2s(j)≥P and −1 otherwise. The integer weight increment is

    d(i,j,b) = floor((floor(b · U(i,j) · 2^(-ρ(j))) + 1) / 2).

The scalar recurrence is

    w(i,j+1) = clip(w(i,j) + d(i,j,b(j)), Wmin, Wmax).

For arbitrary drafted signs β(j), construct candidate pre-sample states

    A(i,j) = w(i,0) + sum[k<j] d(i,k,β(k)).

Accept a block only if:

1. Every cumulative post-update state A(i,j)+d(i,j,β(j)) lies within the legal weight interval.
2. Every β(j) equals the sign calculated from the exact prediction P(A(j),U(j),σ(j)).

**Why accepted results are exact.** Initially A(0) is the true weight state. If A(j) is the true state, condition 2 gives the true update sign. Condition 1 means that update does not clip, so the next true state is exactly A(j+1). Induction establishes every prediction and the final weights. Rejected blocks use the scalar recurrence from the unchanged initial state. This is an ordinary induction argument, not a claim of new verification theory.

The first sample of a band is handled separately using the standard initialization rule. The exactness argument does not rely on scene smoothness, a learned error distribution or the accuracy of the approximate draft. Those factors affect acceptance and speed only.

## Integer arithmetic contract

The tested kernel contract is unsigned16 input, Ω=19, R=64, three to six active difference components, |U|≤262140, 0≤σ≤262140, −9≤ρ≤6 and legal initial weights in [−2097152,2097151]. Full-pipeline fixtures use initial adaptation −1 and final 4/9; the arithmetic stress test also exercises more extreme allowed exponents.

With at most eight samples, each increment's magnitude is at most 67,107,840. Cumulative candidate weight magnitude is below 2^30, so its 32-bit prefix arithmetic does not overflow. Exact dot products, including rejected candidate states, remain far inside signed 64-bit range (a conservative bound is 2^51). The centered R=64 modular calculation therefore admits the simplified exact expression used in the code. Arithmetic signed right shift is assumed for the tested GCC/Clang targets; arbitrary C implementations are not claimed.

The cheap draft deliberately uses modular 32-bit vector operations and truncated starting weights. Its overflow is allowed because the exact acceptance check controls commitment. The AVX implementation can skip exact verification after a range failure; the RVV implementation forms the exact dot products alongside prefix states. Their physical costs can therefore differ.

The scan uses log2(B) slide/add stages. Its arithmetic work is O(C·B·log B); there is no enumeration of all 2^B sign paths. Only one draft is attempted, then one scalar fallback. These operation bounds are not hardware WCET bounds.

## Input and output order

For BIL/BI-depth1 fixtures, the replay source copies one arriving band row into a two-line ring. The within-band methods read current rows at bands ≤z and the previous spectral line. A band-parallel method waits for all current band rows. Golden compressed-body agreement checks the actual ring implementation, and the tests check the number of received rows at completion of the first band row.

This demonstrates input batching, not physical link timing. Scalar and frozen-weight processing have the same one-row availability property. The compressor currently stages a whole current band row; it does not claim immediate output after only eight sensor samples arrive.

For BSQ, the test uses a full replay image. Previous spectral context can require image-sized storage; do not transfer the BIL memory statement to BSQ.

## Covered profile

The complete pipeline covers full prediction, P=3, unsigned16, lossless zero-damping samples, Ω=19, R=64, zero exponent offsets, νmin=−1, νmax=4 or9, interval64, wide-neighbor or narrow-column local sums, and sample-adaptive entropy coding (unary limit32, initial count exponent3, rescaling8, accumulator initialization2). The harness supports one to eight bands. BIL uses BI depth1; BSQ is also exercised.

The fixed-weight comparison follows the published bypass condition Ω=11, exponent offsets5, νmin=νmax=9. Weights are learned from another spatial crop of the same acquisition, rescaled and supplied through a custom initialization table. This is a limited, optimistic calibration experiment, not an exact reproduction of the 2024 authors' multi-sensor corpus.

Expected header bytes are supplied by the independent reference. Bodies are byte-compared, including final byte padding. An independent production header encoder, official full-vector conformance campaign and flight integration are outside the delivered implementation.

## Execution protection

The acceptance check protects semantic equivalence under correct execution. A fault in its own state or instructions can defeat it. ECC, checksums, memory protection, redundant computation and radiation qualification address different requirements and remain separate concerns.
