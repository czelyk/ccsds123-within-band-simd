> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# CCSDS 123 research revision

15 October 2026. **Decision: continue under REVISE, with a narrower claim and stronger comparisons.** This is an AI-assisted internal research record, not external human peer review. No physical performance or acceptance probability is claimed.

## The single research direction

**Question:** When spectral parallelism is genuinely limited, can the existing integer-exact within-band execution transformation provide a useful processing-cost point against the best applicable conventional implementations of adaptive CCSDS 123?

Working title: **Exact Within-Band SIMD for Adaptive CCSDS 123 with Limited Spectral Parallelism.**

The candidate contribution is algorithm engineering: a specific recurrence-preserving execution transformation, its conditional correctness argument, and an experimentally established useful operating region. Exact block filtering, speculation, verification/replay, scans and fixed-weight bypass are established ideas. A new ISA, successful code, benchmark collection or a renamed design framework cannot establish originality. The earlier literature assessment remains applicable: [Sánchez et al.,2022](https://deic.uab.cat/~jbartrina/docs/articles/2022_10-IEEE_GRSL_IUMA_UAB.pdf), [Barrios et al.,2024](https://deic.uab.cat/~jbartrina/docs/articles/2024_01-IEEE_GRSL.pdf), [Benesty–Duhamel,1992](https://www.researchgate.net/publication/3314714_A_fast_exact_least_mean_square_adaptive_algorithm), and [programmable speculation](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/pldi026-vaswani.pdf). The specific combination remains an incremental candidate, not verified high mathematical originality.

The proposal is unchanged. Its qualified profile remains unsigned 16-bit, lossless, zero damping/offsets, Ω=19/R64/P3, full prediction, the two supported local sums, and sample-adaptive entropy coding. Its within-band blocks remain capped at eight samples. No near-lossless extension or general scalability claim has been added.

## What this revision actually completed

Conventional RVV implementations now cover component SIMD at LMUL 1/2, compact spectral groups with natural short vector lengths, native BIP spectral SIMD including automatic vector length, and native BIP scalar/component processing. BIP and BIL compressed orders are both allowed. Baselines avoid unnecessary components in very small band groups; scratch feature storage was reduced to the required width. These are baseline engineering changes, not proposed contributions.

The final Renode checks passed at VLEN 128/256/512/1024. Each width completed 144 deterministic synthetic cases,2016 method comparisons and 4,249,224 mapped-residual comparisons, with zero mismatches. The checks compare compressed bodies, mapped residuals and final weights. Two longer cases actually reach both adaptation exponent caps; merely selecting ν_max=4/9 on small images would not test that distinction. Across four widths this is 8064 method checks, not 8064 independent scenes. Initial checks and their exact source/ELF were archived before the baseline corrections.

A separate RVV Linux pilot was successfully cross-compiled, with manifests and source included. It has not run on a physical board. The Renode binary uses a separate validation harness; model execution time is not target performance. The current spectral RVV helper still gathers features with scalar code. Vector feature extraction or a target-based justification remains necessary before claiming a strongest-target-baseline comparison. The new Ω=12 fixed option is currently a host comparison, not integrated into that adaptive Linux driver.

## A real seven-band content test, with explicit limits

The [CORA Landsat 8 collection](https://doi.org/10.34810/DATA1514) supplies calibrated Level 1 products in unsigned 16-bit little-endian BSQ files. The earliest four acquisitions were selected before reading values/results; all seven supplied bands and full 4096x4096 dimensions were retained. Each image has 117,440,512 samples. All four files matched publisher MD5 values. The earliest acquisition is the retrospective calibration source; the other three are held out.

The products are calibrated, not raw focal-plane data. The publisher retains OLI bands 1–7 and omits bands 8/9; the supplied group is not proof that the instrument has only seven channels or that operations must restrict processing to seven. BSQ-to-BIP reordering was performed outside timing for a resident replay. This tests content in an existing seven-band benchmark, not sensor arrival, DMA or a flight processing budget. Acquisition ordering does not prove flight-time availability of products that were calibrated years later. No samples, dark areas or difficult scenes were filtered out.

The main campaign retained 189 adaptive and 96 fixed-weight timing trials, eight main configurations and one preselected ν_max=4 sensitivity. Ten adaptive and four default-fixed prefix checks matched the unchanged NTNU model. Independent checks cover two complete 4096-pixel rows; full images are checked against C references. Frequencies were not locked, and background downloading/checksum activity overlapped early cases. All trials remain; the medians are exploratory, not mission-population confidence intervals.

| Acquisition | Local sum | Within-band, ns/sample | Best tested conventional adaptive baseline, ns/sample |
|---|---|---:|---:|
|2013-03-22, training | Narrow column |21.70 |18.02, native BIP spectral 8 |
|2013-03-22, training | Wide neighbor |21.56 |19.62, native BIP spectral 8 |
|2013-11-03, held out | Narrow column |20.39 |17.06, compact spectral 8 |
|2013-11-03, held out | Wide neighbor |22.79 |19.63, compact spectral 8 |
|2014-02-04, held out | Narrow column |19.94 |16.50, compact spectral 8 |
|2014-02-04, held out | Wide neighbor |20.80 |18.18, compact spectral 8 |
|2014-06-19, held out | Narrow column |19.66 |16.50, native BIP spectral 8 |
|2014-06-19, held out | Wide neighbor |20.84 |18.11, compact spectral 8 |

The proposal beat the best tested sequential/single-band path by 1.230–1.366x, but lost to conventional spectral SIMD in every main case. Conventional alternatives used about 9.0–17.2% less elapsed time, at the same compressed size for each configuration. The sensitivity also favored spectral SIMD. Small differences between conventional implementations should not be overinterpreted.

**Interpretation:** seven bands do not by themselves make this technique valuable. The tested resident seven-band case is a negative result for the proposed primary advantage. More repetitions of similar benchmarks are not needed to rescue that story.

## Adaptation and independent contexts

On the three held-out acquisitions and both local sums, default fixed Ω=11 outputs were 5.40–8.15% larger than adaptive Ω=19. Earlier-acquisition-trained fixed outputs were 1.12–9.32% larger. This is one calibration policy, not proof that all fixed predictors fail. Precision also changes, so the whole difference cannot be attributed solely to adaptation.

Preserving adaptation can therefore retain bytes in these tested comparisons. However, conventional spectral SIMD already preserves the same adaptation and compressed size while running faster here. **The value of adaptation does not establish the value of our execution method.** This distinction is central to the revised paper.

Independent horizontal stripes were also encoded with separate adaptive contexts and actual CCSDS headers. Relative size changes across all main cases were:

| Stripes | Size change range |
|---:|---:|
|2 |−0.622% to +0.635% |
|4 |−0.617% to +1.582% |
|8 |−0.682% to +3.131% |

For the wide-neighbor configurations, even eight stripes ranged from −0.682% to +0.220%; wide-neighbor also gave smaller full-image outputs than narrow-column in every selected acquisition. We must not emphasize narrow-column's larger reset cost while ignoring this stronger alternative.

These measurements characterize reset cost and sequential encoding work. Parallel tile/context SIMD was not implemented or timed. Mission-specific container/index/packet overhead is also excluded. Nevertheless, the results make independent contexts a serious baseline for any buffered workload. Neither negligible reset cost nor a parallel speedup can be presumed universally.

## A stronger fixed-weight profile was checked

For this exact lossless zero-damping profile, local differences obey |u|<=4*(2^16−1)<2^18. With nu_min=nu_max 9, offsets 5 and Ω=12, the update shift is 18; every possible signed update rounds to zero. The scalar check exhaustively evaluated 524,281 possible integer differences. At Ω=13 that unconditional bound no longer holds. This is a straightforward profile-specific application of existing weight bypass, not a new mathematical contribution claim.

Six independent-reference prefix checks confirmed default/custom weights for both local sums and the sensitivity table; all active weights from the second sample onward remained constant and compressed outputs matched. Default Ω=12 weights are exactly twice default Ω=11 weights, so their normalized predictions are unchanged: nine full-case identities were verified without repeating unnecessary default timings.

Newly rounded earlier-acquisition-trained Ω=12 tables were evaluated in 42 timing trials. Their held-out main outputs were 1.126–9.328% larger than adaptive Ω=19, and slightly larger than the Ω=11 alternatives in this pilot. More precision did not improve these learned static tables. The ν_max=4 sensitivity difference was+7.479%. These results remain a separate campaign; no paired timing comparison with the earlier campaign is claimed. The precision difference from Ω=19 remains.

The first validation attempt failed because my assertion included the reference model's unused first-sample weight storage. Source inspection and a recorded diagnostic established that initialization occurs at t=1; all later active weights were constant. The failed driver, partial records and diagnosis are preserved. No performance trials from that failed attempt were used.

## Application evidence and the remaining scientific gate

The [CCSDS corpus description](https://ccsds.org/Pubs/120x2g1s.pdf) identifies genuine raw six-band D8 Landsat and four-band D10 Vegetation workloads. They are relevant existing data classes. The official download endpoint returned 403 here, so those images were not tested. Padding them into our D16 profile would be an invalid substitute for profile-matched evaluation.

The [2025 NASA-hosted LandIS study](https://ntrs.nasa.gov/api/citations/20250008078/downloads/LandIS_compression_final.pdf) also establishes per-band CCSDS 123 processing as a real application context. It uses relative-error near-lossless/hybrid coding and planned FPGA implementation, outside our qualified profile. Separate band coding does not forbid batching independent band contexts. Neither that mission's data rate nor its requirements can be assigned to our prototype.

The remaining question is consequently specific: can a real, profile-matched workload with limited usable parallel contexts yield a meaningful cost advantage on a real vector target? A convenient band subset, forced output order, arbitrary percentage threshold or invented arrival deadline cannot establish it.

## Bounded next work and decision

The project remains **REVISE**. The tested seven-band resident use case provides no host advantage, while the specific exact execution transformation remains functionally sound and faster than tested sequential paths. Neither result establishes the target outcome for a genuinely constrained raw workload.

Before a paper-level GO, fix one actual workload/profile and its source-supported processing/storage/output budget. Obtain the relevant raw corpus or mission data with provenance, and implement any required dynamic-range support without changing values. Separate training from held-out acquisitions. Then complete the applicable conventional comparisons, including vector feature extraction, independent contexts and stronger fixed profiles, with comparable target optimization effort. Compare another established codec if the selected requirement permits it and makes it a credible operational alternative.

Physical tests must establish complete-compressor cycles/time, energy boundary, memory/stack/code and source-to-output behavior on that target. The prepared executable supports initial correctness and resident measurements. It does not include all mission adapters or every required alternative. A limited falsification pilot can expose a poor target cost point; a win against these functional prototypes would still require the stronger comparisons before publication claims.

If those alternatives cover the useful operating region, stop this paper. If the exact transformation occupies a meaningful additional point under the documented use, its incremental algorithm-engineering contribution can be evaluated for IAC. Ordinary negative benchmarks alone will not be relabeled as novelty. No unrelated topic search or further unbounded implementation sweep is recommended.

The suitable session remains D1.2, Technologies that Enable Space Systems, with the 28 February 2027 abstract deadline in the [official Call for Papers](https://www.iafastro.org/assets/files/events/iac/2027/IAC2027_Call_for_papers.pdf). The same call restricts AI assistance for key scientific authoring tasks. Our assistance exceeds language editing; IAF clarification remains necessary. A candid draft is prepared for human review and has not been sent. Hardware results or rewriting do not automatically resolve eligibility.

All source, raw positive/negative results, failures and reproduction instructions are retained. `README.md` is the entry point. The strongest legitimate rejection reason remains the absence of a demonstrated distinctive design value against established alternatives, not the mere absence of a physical board.
