> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# Revised investigation protocol

Recorded 15 October 2026 before the new RVV baseline checks. Status: REVISE; no physical performance conclusion.

Research question: when spectral parallelism is genuinely limited, does the existing exact within-band execution transformation offer a useful cost point against the strongest applicable conventional execution methods?

The method, its eight-sample cap, historical source and measurements remain unchanged. The next implementation work is limited to missing conventional RVV baselines and functional checks. Do not tune the proposal using new workload outcomes.

Required conventional comparisons: fused scalar, component SIMD, compact band SIMD with natural short vector lengths, native-BIP spectral SIMD, and native-BIP scalar execution. Independent spatial-context/tiling parallelism is also a required experimental alternative when a workload permits it; include reset, framing, compressed size and buffering costs. It must not be excluded because its compressed bitstream differs.

Functional experiment: compile the same new harness for host/scalar and RVV. In Renode, test VLEN 128/256/512/1024, both supported local sums, nu_max 4/9, full-range constant/checker/random inputs, small/tail widths, and band counts including 1/2/3/4/6/8/9/17/120/128. Compare BIL output byte-for-byte with fused scalar. Compare BIP output byte-for-byte with a conventional scalar BIP implementation and compare mapped residuals/final weights across output orders. Renode timing must never be reported as board timing.

Workload gate: the CCSDS Green Book documents raw six-band D8 Landsat and raw four-band D10 Vegetation data. These are credible pre-existing low-spectral-parallelism data classes; their names are not proof of an operational need for this method. The official corpus returned 403 in this environment. No such scene has been downloaded or tested in this revision. The existing code's D16 profile must not be silently substituted for D8/D10. GICI L1 images in raw binary containers are processed products, not raw focal-plane samples.

The 2025 NASA-hosted LandIS study provides another relevant per-band CCSDS 123 application, but uses relative-error near-lossless coding and an FPGA implementation plan. Our lossless zero-damping method cannot be claimed to meet that mission profile or its data rate. Separate per-band coding also does not forbid batching independent band contexts.

No new mission deadline, required compressed-byte identity, or acceptance percentage will be invented. Report source-supported constraints separately from modeling assumptions and measured operating envelopes.

Before a hardware campaign: obtain a representative corpus with provenance and its actual dynamic range; select an operationally relevant profile/budget; complete profile-matched correctness; retain strong scalar/vector/tiled/fixed-weight alternatives; separate calibration/training from test acquisitions. Parameter sweeps must be bounded and recorded before examining outcomes.

A physical pilot must measure complete-compressor cycles/time, code and working memory, output readiness with actual source/sink behavior, fallback tail costs and joules per completed image. The decision must depend on a meaningful measured trade-off under the documented use, rather than an arbitrary 1.20x threshold. Stop this paper if established alternatives cover the useful operating region and the special transformation contributes no additional knowledge.

IAF policy clarification is a separate unresolved eligibility gate. Prepare an accurate description of AI assistance for human review; do not contact IAF without authorization. A new hardware result or human rewrite is not assumed to resolve that question.
