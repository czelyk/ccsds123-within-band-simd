> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# GO for physical testing: bit-exact block speculation for streaming spacecraft image compression

**Follow-up review:** read the newer [fair skeptical assessment](FAIR_REVIEW.md) before acting on this report. The prototype remains suitable for a small falsification experiment, but it is **NO-GO for commitment as a strong IAC topic on current evidence**. Mission necessity, smaller-batch latency baselines and broader exact-block prior work remain unresolved. The earlier statement that pre-hardware work was complete referred too broadly to completed software checks; scientific prerequisites remain. The original technical assessment below is retained for traceability.

**Decision, 15 October 2026: GO for a defined physical evaluation.** The recommended topic is **“Bit-Exact Within-Band Vectorization of Adaptive CCSDS 123 Compression.”** This is a software algorithm and embedded implementation study in on-board data handling. It is not a claim of a new mathematical theorem, proven high originality, flight readiness, or assured IAC acceptance.

The evidence now justifies testing a concrete implementation on vector-capable embedded hardware. It does not justify submitting a paper claiming demonstrated spacecraft throughput or energy savings. The latter results still need physical measurements and representative raw payload data.

## The engineering problem

The adaptive predictor in CCSDS 123 updates its weights after each sample. The next sample needs the updated weights, which creates a serial dependency inside a band. Parallel processing across bands is established, but requires multiple band inputs to be available. In a line-interleaved input stream, waiting for those inputs adds batching latency. Freezing weights or restarting image tiles changes the predictor's behavior and compressed output.

The research question is: **Can software exploit consecutive samples inside the current band, preserve the adaptive compressed result exactly, and improve the throughput–latency trade-off on an embedded vector processor?**

This ordering is relevant to payloads: the closest 2024 work specifically discusses line-interleaved data from pushbroom sensors. It is not a claim that all spacecraft imagers use this order. [Barrios et al., 2024](https://doi.org/10.1109/LGRS.2024.3362376)

## What the implementation does

For a block of at most eight samples, a cheap 32-bit vector calculation guesses the signs that drive the weight updates. Prefix sums reconstruct candidate weight states. A full 64-bit calculation then checks the prediction signs at those states. The block is accepted only if every sign agrees and no update would saturate a weight. Otherwise, the original scalar recurrence processes the block once.

The guess may be inaccurate, including because its arithmetic wraps. It cannot directly determine an accepted output. There is one speculative attempt per block, followed by a bounded fallback; there is no convergence loop.

RISC-V vector hardware enables this execution strategy through vector shifts, slides and widening multiplication. It was chosen after identifying the recurrence problem. Its mere use is not the contribution. Space relevance is supported by the vector-capable PIC64-HPSC architecture, although no performance on that processor has been measured here. [Microchip PIC64-HPSC](https://www.microchip.com/en-us/products/microprocessors/64-bit-mpus/pic64-hpsc)

## First skeptical review: originality

| Closest established work | What is already established | What remains distinct in this candidate |
|---|---|---|
| Sánchez et al., 2022 | Bit-identical acceleration; removing quantization from the feedback path; computing both possible weight updates eagerly and selecting the correct result. | Software drafting and checking of a multi-sample trajectory, using prefix reconstruction rather than exhaustive enumeration of sign paths. |
| Barrios et al., 2024 | Standard-compliant constant-weight operation, partial updating and exogenous weight generation; substantial hardware acceleration with a compression trade-off. | Preserving the selected adaptive predictor's actual output without calibration or freezing. |
| Parallel band/tile implementations | Spatial/spectral parallelism and the cost of limited band parallelism are longstanding topics. | Exploiting samples within an existing band without introducing a tile restart. |
| General speculative execution and prefix algorithms | Speculation, rollback, parallel scans and saturated-accumulation transformations are established techniques. | A specific CCSDS software decomposition and an experimentally testable deployment trade-off, not ownership of those general techniques. |

The two closest papers were obtained from their authors' public copies and their methods were examined. Their overlap is substantial and must be acknowledged. Neither examined method contains this particular approximate-draft / prefix-state / exact-block-check software procedure. That is evidence for a bounded contribution, not proof that no related publication exists anywhere. [2022 author copy](https://deic.uab.cat/~jbartrina/docs/articles/2022_10-IEEE_GRSL_IUMA_UAB.pdf), [2024 author copy](https://deic.uab.cat/~jbartrina/docs/articles/2024_01-IEEE_GRSL.pdf)

**Originality judgment:** plausible, specific engineering originality; mathematical originality is limited. A paper presented as “the first speculative CCSDS predictor,” “the first bit-exact acceleration,” or “CCSDS on RISC-V” would have a serious originality problem. The defensible contribution is the block execution method plus measured conditions where it is useful. Hardware results must make that contribution consequential.

## Second skeptical review: does it offer a useful advantage?

The baseline comparison was strengthened several times. It now includes specialized fused scalar code, staged scalar code, eager computation of both update signs, SIMD across bands, and a calibrated constant-weight configuration. The inter-band implementation retains a prediction row rather than an unnecessary full-frame prediction array.

Completed host measurements use an Intel i7-12700H, GCC optimization, one pinned core, nine trials with rotated variant order, and repeated complete compression from raw integer samples to packed compressed bodies. These are exploratory host results, not embedded performance claims.

| Finding | Consequence |
|---|---|
| On six line-interleaved configurations from three processed airborne scenes, speedup over the best tested scalar/eager implementation was **1.23–1.27×**, geometric mean approximately **1.25×**. | A useful signal survives complete compression, not just an isolated predictor benchmark. |
| Band SIMD was approximately tied on those six-band cases when all band rows were available. | There is no demonstrated general throughput superiority over band parallelism. |
| The row-at-a-time path completed the first compressed band row after receiving one band row; the tested band-SIMD path required six. Scalar and fixed-weight paths also required one. | Lower batching is a property of the execution arrangement; it is not uniquely invented by this method and is not a measured physical latency. |
| A real 256×256×8 Pavia crop also retained a host improvement over the best scalar baseline. | The positive result is not restricted to the smallest crop. It is still processed airborne data. |
| Constant and checkerboard inputs caused slowdowns. | The method is not universally faster, and high acceptance of speculative blocks alone does not predict speedup. |
| The calibrated fixed-weight implementation was faster. Its total compressed size ranged approximately from **1.30% smaller to 1.08% larger** than the corresponding adaptive configuration on these small cases. | Fixed weights are a serious alternative. The candidate does not dominate them. Calibration used another spatial crop of the same acquisition, an optimistic and limited proxy for exogenous calibration. |

The narrow practical case is retaining a chosen adaptive compression behavior while accelerating its current-band processing. If a mission accepts fixed weights and their performance across its complete data distribution, the established bypass method may be preferable. If the application can wait for multiple bands, established band SIMD may be preferable. A dedicated FPGA can also be a better system choice; the present study makes no claim to outperform FPGA compressors.

## What was actually executed

- **48 native fixture cases**, covering both local-sum modes, two adaptation settings, both BSQ and line-interleaved output, calibrated fixed-weight configurations, varying band counts, a larger real crop, and synthetic boundary cases. Applicable implementations matched the independent compressed-body bytes.
- **Address and undefined-behavior sanitizers** passed those 48 fixture cases after a benchmark buffer-cleanup leak was fixed.
- A kernel test checked **65,914 predicted values**, plus final weight state, independent reference values, tails, chunk continuation, extreme weight states and adversarial arithmetic. No mismatches were observed.
- The actual RISC-V vector kernels and complete compressor ran in **Renode at 128-, 256-, 512- and 1024-bit vector register sizes**. At each size, 102 complete compression runs checked **4,302,200 body bytes**, with no mismatches or traps. The same binary was used across vector sizes. The block cap remains eight samples; these runs do not demonstrate performance scaling with larger registers.
- The line-interleaved arrival-count condition was also checked in the Renode suite.
- A static RISC-V Linux benchmark executable was successfully cross-compiled. It has not been executed on physical hardware.

Expected outputs came from the unmodified, pinned [NTNU high-level verification model](https://github.com/NTNU-SmallSat-Lab/ccsds123_issue_2_verification_model), associated with its WHISPERS 2024 publication. Its authors report validation against CCSDS vectors. We did not independently obtain and rerun the official CCSDS vector corpus; its download endpoint was inaccessible. This distinction matters.

The implementation compares compressed **bodies**; the configuration/header bytes come from the reference fixture. It is not a new, independently validated header encoder or a full-standard conformance certification.

## Scope, assumptions and overhead

The complete experimental profile is unsigned 16-bit samples, lossless operation, zero sample damping, three prediction bands, full prediction mode, register size 64, weight resolution 19, zero exponent offsets, initial adaptation parameter −1, final parameter 4 or 9, and interval 64. Current complete-pipeline fixtures contain one to eight bands. The broader standard, near-lossless operation, arbitrary parameters and full hyperspectral cubes are not claimed as implemented coverage.

Exactness assumes correct execution of the arithmetic and checks. This is not a radiation fault detector and is not an alternative to ECC or redundant execution. The correctness argument and integer bounds are in `METHOD.md` in the kit.

The implemented prefix scan uses logarithmic scan stages: do not describe it as a new linear-work scan. Its arithmetic work is proportional to C·B·log(B), with B≤8. A failed attempt adds scalar work; bounded attempts do not establish a hardware WCET.

For line-interleaved replay, predictor input enters a two-line ring. The proposed path uses 4·bands·width bytes for that ring and 40·width bytes for staged row arrays, plus state and stack. These are requirements derived from the code paths, not full-process RSS measurements or a memory-optimality claim. The harness also retains a complete replay fixture, reserves output memory, and allocates competing baselines' buffers. A production source/sink adapter is still needed for a flight system.

## Why an IAC reviewer could still reject it

1. **Incremental contribution:** the reviewer may consider the method an unsurprising application of speculation and scans. Physical results must establish a useful new execution option, not merely correct code.
2. **Weak space relevance:** a desktop result or a COTS board alone cannot establish flight-system benefit. The paper needs a credible payload ordering, processor budget and application context.
3. **An easier alternative wins:** fixed weights, band SIMD, tiling or an FPGA may better meet the actual mission requirements. Those alternatives must remain visible in the paper.
4. **Limited data:** the current real fixtures are processed airborne images, often spectral subsets, not a representative raw spacecraft corpus. Their timing statistics cannot establish general mission performance.
5. **Architecture dependence:** RVV instruction latency, register pressure, caches and memory traffic may erase the host speedup or increase energy consumption.
6. **Overstated guarantees:** functional Renode tests cannot demonstrate physical timing, energy, radiation tolerance or complete CCSDS conformance.

These are surviving limitations, not arguments to conceal. They define the physical study's rejection criteria.

## Physical tests and paper decision

The kit contains the actual vector implementation, all comparison methods, reference fixtures, source provenance, raw logs, a build script, a validation/timing runner and a measurement protocol. A vector-capable embedded board can now be used to measure correctness, complete-compressor latency, throughput, energy and stack/working memory. A space-oriented engineering model would strengthen external validity; a BPI-F3/K1 is a documented RVV 1.0 development platform for the initial physical experiment. No HPSC or K1 results have been invented. [BPI-F3 documentation](https://docs.banana-pi.org/en/BPI-F3/BananaPi_BPI-F3)

The protocol predefines a useful target: at least a 20% geometric-mean improvement over the best applicable bit-exact baseline on an independently selected representative corpus, with a useful latency or energy benefit and acceptable worst-case behavior. This is an engineering decision threshold, not an IAC acceptance rule. If hardware gains are negligible, depend on cherry-picked scenes, or lack a credible mission use case, the acceptance-focused paper is **NO-GO**.

Before finalizing the paper, demonstrate the hardware advantage, add independently acquired raw payload/spacecraft data, establish a concrete system requirement, and repeat a current literature check. Do not claim high originality merely because these tests pass.

## IAC fit and eligibility

D1.2, **Technologies that Enable Space Systems**, explicitly includes software techniques and component/system innovations. The current call evaluates technical merit and session relevance, asks for original unpublished work, and sets an abstract deadline of 28 February 2027. Technical fit is defensible; acceptance is uncertain. [Official IAC 2027 call](https://www.iafastro.org/assets/files/events/iac/2027/IAC2027_Call_for_papers.pdf)

There is a separate unresolved eligibility issue. The same call restricts AI from performing “key authoring tasks,” including producing scientific work and recommendations, and requires disclosure. This work includes substantial AI assistance in topic development, implementation and analysis. Obtain an IAF clarification covering that use before treating the work as an eligible submission. Human rewriting or physical testing alone should not be assumed to resolve the policy. The technical GO for physical experimentation does not certify IAC eligibility.

**Final judgment:** the defined software pre-hardware checks support **GO for physical testing of this one topic**. The candidate has a concrete method, a credible but narrow advantage, and clear ways to fail. It is not yet a validated IAC paper or a promise of acceptance.
