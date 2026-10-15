> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# Processed multispectral pilot — bounded protocol

Recorded before reading image samples or timing the new dataset. Selection file: `evidence/landsat8-selection.json`. Four earliest acquisitions from the publisher's21-file collection; retain all seven supplied bands and full 4096x4096 dimensions. No mask, clamp, resampling, normalization or rejection of low/high entropy content.

This is a processed Level 1 workload. Its raw binary container is not evidence of raw sensor values. Native OLI quantization must not be confused with the dynamic range of the delivered 16-bit product. Reformatting BSQ files into BIP for a resident replay is outside timing and provides no mission data-arrival claim.

Question: does the within-band host execution point survive on naturally seven-band scenes against strong conventional alternatives, and how much rate penalty would independent spatial-context resets incur?

For both local sums at nu_max 9, compare fused scalar 0, unchanged within-band 2, compact band 7group 8, component 8, nativeBIP9groups 4/8, and nativeBIPscalar 11. Use three rotated trials, same available core, no concurrent timing jobs, retain all raw trials and verify every body against the appropriate output-order reference. Report frequency as uncontrolled. Repeat nu_max 4 for the first held-out acquisition/narrow-column case only, a preselected sensitivity, not a tuned best result.

Before full timing, compare the first two full-width rows of each scene/narrow-column nu_max 9 with the unchanged NTNU model in BIL and BIP output orders. Full images are checked against C references, not independently recomputed by Python. All inputs must match their publisher-file MD5 when available, and retain locally computed SHA256 hashes.

Fixed-weight alternatives: compare both default and earlier-acquisition-trained Ω=11 tables with offsets 5, nu_min=nu_max 9. Keep the Ω=19 adaptive baseline and disclose that precision also changes. Training data is only the earliest acquisition; report its work separately and do not count it as a held-out scene. Calibrated products are retrospective: acquisition ordering does not prove flight-time availability. Include actual header sizes from the reference header generator. No same-scene whole-image oracle training.

Independent-context sensitivity: split each full image into 2/4/8 equal horizontal stripes; compress all seven bands of each stripe with independently reset adaptive state, adding one actual header per stripe. Measure compressed bytes and sequential encoding work only. This characterizes reset cost; it does not implement or time parallel tile SIMD, and must not be reported as its speed. Buffering and arrival costs remain separate unresolved system questions.

Interpretation: a host win is a mechanism result. A host loss is retained and weakens the direction. Neither establishes target RVV speed, energy or a spacecraft requirement. Small reset penalties strengthen the obligation to compare parallel independent contexts on the target. Do not turn ordinary benchmark characterization into an originality claim.

## Stronger fixed-profile amendment, before its results

A profile-specific arithmetic review shows that Ω=12 is sufficient for unconditional zero weight updates in this exact lossless/zero-damping profile. Every local difference satisfies |u|<=4*(2^16-1)<2^18; with nu_min=nu_max 9 and offsets 5, rho=9+16-12+5=18. Thus ((sign*u >>18)+1)>>1 is zero. Ω=13 no longer guarantees zero for the full allowed input range. This is a straightforward bound on an established technique, not a claimed contribution.

After the frozen main pilot finishes, build and separately evaluate Ω=12 fixed scalar/SIMD on the same nine cases, with default weights and earlier-acquisition-trained weights; relearn the three source tables at Ω=19 and round by 7 bits, rather than reconstructing them from previously rounded Ω=11 weights. Validate custom/default prefixes independently for both local sums and the sensitivity table; retain Ω=11 results. Use three rotated fixed scalar/SIMD trials and include actual headers. Do not compare timing samples across campaigns as though paired. All precision-vs-adaptation qualifications still apply.

Stripe byte counts include CCSDS headers but omit a mission-specific container/index/packet overhead. They are not complete flight framing costs.

Before running the Ω=12 follow-up, remove unnecessary repeated default-weight timings: default Ω=12 weights are exactly twice default Ω=11 weights, so their normalized predictors and bodies are identical. Validate that identity on every full case and retain independent default-prefix checks. Run the three paired timing trials only for the earlier-acquisition-trained Ω=12 alternatives, where the extra precision can actually change prediction and coding work. Preserve all prior Ω=11 timings.
