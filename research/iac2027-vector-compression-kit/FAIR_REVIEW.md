> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# Fair skeptical review of the CCSDS 123 vectorization candidate

15 October 2026. This is a fresh assessment of the existing sources, implementation and recorded results. It is not an external peer review. No new physical results are claimed, and no alternative topic is proposed.

**Decision: NO-GO for committing to this as a strong IAC 2027 paper on the present evidence. A small, clearly scoped physical falsification experiment remains reasonable, but a major hardware campaign should follow—not substitute for—resolving the mission requirement and baseline gaps.** The previous technical GO was permission to investigate hardware performance, not validation of a strong paper. Describing all pre-hardware work as complete was too broad. Code preparation is complete for the supplied experiment; scientific prerequisites remain.

## 1. The largest weakness is the reason to preserve the adaptive bitstream

The proposed method preserves one chosen adaptive predictor's compressed result. This is stronger than preserving the original image. A standard-compliant fixed-weight compressor in **lossless mode also reconstructs the original pixels exactly**. It changes prediction behavior and compressed size, not image fidelity. [CCSDS 123.0-B-2](https://ccsds.org/Pubs/123x0b2e2c3.pdf)

Consequently, bitstream identity is an engineering property, not automatically a mission benefit. The paper needs a reason to retain this adaptive configuration: for example, demonstrated compression robustness across changing scenes, a binding downlink/storage budget, or an existing configuration whose modification has a quantified integration cost. Those are hypotheses to establish, not facts demonstrated here.

The fixed-weight comparator used about 18–21% less host time than the proposed method on the six BIL cases. Total compressed size in those cases changed by roughly −1.30% to +1.08%. It is a serious challenge, not an intentionally inferior baseline. However, its calibration used another spatial crop of the same acquisition, including rows later than the tested crop. That optimistic experiment does not prove a causal onboard calibration method or general cross-scene superiority. Neither method has established a mission-level advantage over the other.

## 2. Mathematical originality is low; specific implementation originality remains plausible

The correctness argument is ordinary induction. Guessing signs, reconstructing candidate states with a prefix calculation, checking those states and reverting to scalar execution combines established ideas. The fact that the derivation is correct does not make the mathematics new.

The closest CCSDS work already establishes bit-identical dependency reduction and eager computation of both sign updates. The 2024 work removes weight updates under a compliant parameter configuration and studies calibration and compression penalties. The specific multi-sample draft/check implementation was not identified in those two examined papers, but that is a bounded distinction. [Sánchez et al., 2022](https://deic.uab.cat/~jbartrina/docs/articles/2022_10-IEEE_GRSL_IUMA_UAB.pdf), [Barrios et al., 2024](https://deic.uab.cat/~jbartrina/docs/articles/2024_01-IEEE_GRSL.pdf)

The broader literature is also relevant. Exact block formulations of adaptive LMS filtering existed in 1992; speculative vector execution and replay are established. The 1992 institutional record establishes the broader exact-block precedent, not that this CCSDS integer/sign/clipping implementation has already been published. Its relationship to the proposed decomposition needs explicit examination before claiming comprehensive originality. [Benesty and Duhamel](https://cris.technion.ac.il/en/publications/a-fast-exact-least-mean-square-adaptive-algorithm-2/), [Sun et al., 2021](https://www.cl.cam.ac.uk/~tmj32/papers/docs/sun21-isca.pdf)

The defensible claim is a particular software execution transformation for a stated CCSDS profile. A reviewer could still regard it as routine optimization. Strong experimental consequences can make an engineering contribution worthwhile; they cannot retroactively create a new theorem.

## 3. The headline speedup is against scalar code, not the strongest available competitor

The recorded 1.23–1.27× BIL speedup over the best tested scalar/eager implementation is real evidence for the tested host and data. It corresponds to roughly 19–21% less execution time, not a 25% time reduction.

Against the implemented band SIMD comparator, the six host ratios lie about 0.995–1.017×: effectively tied, without an established statistically meaningful throughput advantage. The proposal therefore needs a useful latency, memory, calibration or compression trade-off. It cannot be presented as general superiority over conventional SIMD.

The comparison is much stronger than an untuned reference model comparison. Specialized fused scalar, staged scalar and eager-sign methods are included. Nevertheless, all performance implementations were produced within the same development effort; independent optimized software, compiler sensitivity, profiling and targeted ablations remain useful checks. Implementation differences must not be mistaken for algorithmic necessity.

In particular, the eight-sample cap and eight-bit draft truncation are design choices, not established optima. Profiling and controlled changes to block size, drafting precision and preprocessing would explain where the benefit comes from and whether the draft/check complexity earns its cost. These are useful experimental strengthening steps, not requirements to support every standard configuration.

## 4. The current latency argument is incomplete and the baseline imposes batching

In `src/band_rvv.inc`, the band comparator calls `prepare_rows(f,y,-1)` before processing vector groups. This loads every current band row. The within-band path loads the current band row. The first-row arrival count therefore verifies those programmed choices. It does not establish an unavoidable lower bound on band SIMD latency.

For example, a band implementation can trade utilization for smaller groups as inputs arrive. The 128-bit RVV execution already processes a six-band image in multiple vector groups, while the harness still waits for all six rows. A fair latency study needs smaller band groups, a credible arrival schedule and identical deadlines. This does not prove the proposed method will lose; it makes the current latency evidence incomplete.

The count also omits arrival time, computation overlap, backpressure, DMA, output-byte availability and packetization. Completion of a band-row loop is not automatically completion of a transmitted packet. Scalar and fixed-weight paths share one-row availability. A real deadline or resource constraint must make the throughput/availability combination matter.

## 5. Data-dependent slowdowns are already observed

Derived from the existing host medians:

| Input | Proposed speedup over best scalar | Equivalent change in execution time |
|---|---:|---:|
| Constant | 0.883–0.905× | About 10–13% longer |
| Checkerboard | 0.621–0.746× | About 34–61% longer |
| Noise | 1.045–1.064× | About 4–6% shorter |

Checkerboards are stress inputs, not evidence of typical mission imagery. These examples nevertheless refute universal acceleration. Constant cases accepted all speculative blocks and still ran slower, showing that acceptance alone is not an adequate performance selector.

A rejected block performs draft/check work and then scalar work. Bounded attempts do not imply a useful WCET. A selection policy might help, but its own cost, mistakes and deadline behavior need evaluation; generic adaptive dispatch would not automatically add originality.

## 6. The corpus is too narrow for general mission conclusions

There are three processed airborne acquisitions, not 48 independent real scenes. Most test cases are alternative configurations, crops or spectral subsets. The first six adjacent bands of a hyperspectral acquisition are not equivalent to six independently specified multispectral channels. Their spectral correlation and numerical range can affect prediction and sign stability.

The primary BIL timing claim uses one final-adaptation setting; additional adaptation settings were exercised in BSQ. Current full-pipeline support stops at eight bands. Full hyperspectral cubes, different bit depths, near-lossless operation, nonzero damping, independent scenes and calibration transitions remain outside the demonstrated coverage. The 256×256×8 crop is useful scale evidence, but still not a full mission corpus.

Processed airborne data are legitimate development inputs. Raw spacecraft data are not a universal prerequisite for every IAC software paper. The requirement is justified representativeness: actual payload data or a transparent, credible workload model. Neither a familiar dataset name nor repeated cropping establishes that.

## 7. Correctness evidence is a strength, with precise boundaries

The draft cannot directly commit an unverified approximation. Under the stated arithmetic bounds, range checks and correct execution, the acceptance argument is sound. Matching an independent Python reference and running actual RVV code at four vector sizes provide substantial implementation evidence. These should receive credit.

However, millions of checked output bytes are correlated trace checks, not millions of independent scientific trials. They do not establish all-input correctness of the C implementation, complete standard conformance, timing determinism or a probability of failure. Reference-provided headers and unavailable official vector testing remain limitations. A supported narrow profile can be a valid paper scope if it is used by the target application and stated clearly.

This is not a fault-tolerance method. ECC, checksums and redundancy are not appropriate replacement baselines for its performance claim. Equally, exact checking must not be advertised as protection against radiation faults in the checker, state or instructions.

## 8. Embedded speed, energy and scaling are unproven

AVX2 host results do not determine RVV performance. Widening multiplication, slides, reductions, vector-to-scalar transfers, register pressure and memory traffic can change the balance. Renode establishes functional execution here; its virtual timing does not establish board timing or energy.

The block cap is eight samples. At 256-bit and larger register sizes the tested method still uses no more than eight 32-bit lanes; running at 512 or1024 bits does not demonstrate performance scaling across those sizes. There is no current multicore result.

Extra arithmetic can increase energy even if it reduces time. The relevant system comparison may also include downlink/storage consequences of a different predictor configuration. No measured energy advantage exists yet.

## 9. Memory and integration are manageable hypotheses, not completed system evidence

The BIL path's two-line input ring and staged scratch arrays are concrete. Derived buffer sizes are useful; they are not a measurement of the integrated encoder's RAM, stack, cache contention or DMA compatibility. The harness holds the whole replay input and allocates competing methods' buffers. It is not a deployed sensor-to-telemetry pipeline.

The present prototype is implementable enough for a small target experiment. That is a feasibility strength. A flight-board result is not mandatory for an algorithm paper, but a COTS board cannot be called evidence of HPSC performance, radiation tolerance or flight readiness. A credible payload/processor budget is still required.

## 10. IAC fit exists; acceptance strength and eligibility do not follow from it

The on-board software/compression subject fits D1.2's technology scope. IAC can value an experimentally convincing engineering contribution without a new mathematical theorem. The present risk is that the paper reduces to a small optimization with no demonstrated spacecraft consequence. More benchmark cases alone would not cure that problem.

The previously proposed 1.20× threshold is a declared engineering screening target, not an IAC rule or a substitute for a mission requirement. A smaller gain that closes a real deadline can matter more than a larger gain with no practical consequence. Any revised criterion should be justified and fixed before seeing target results.

There is also the separate AI eligibility issue. The official call restricts AI from key authoring tasks including scientific work and recommendations and requires disclosure. This development includes substantial such assistance. An IAF clarification is required before assuming an eligible submission; human rewriting and physical measurements cannot be assumed to settle that interpretation. [Official IAC 2027 call](https://www.iafastro.org/assets/files/events/iac/2027/IAC2027_Call_for_papers.pdf)

## What would change the decision

Resolve these gates in order:

1. Identify a credible payload requirement that makes the combination of adaptation, availability and execution cost valuable. Do not invent a byte-identity constraint to exclude faster lossless alternatives.
2. Compare the exact decomposition to exact-block adaptive filtering and broader speculative-vector methods; write a precise, bounded contribution statement.
3. Evaluate the strongest relevant latency/throughput alternatives, including smaller band groups and a realistic fixed-weight calibration policy. Keep negative results.
4. Choose representative held-out inputs and required parameter profiles before tuning to target measurements. State how they represent the intended payload.
5. Measure target correctness, sustained throughput, scheduled output latency, energy, resource use and data-dependent slowdowns. Use the same conditions for competitors and include uncertainty.
6. Resolve IAC policy eligibility before making a submission commitment.

**Final assessment:** the prototype is technically credible, but practical necessity is currently the weakest link and originality remains an incremental claim needing tighter comparison. A small experiment can be worthwhile; this is not yet a trustworthy, high-confidence IAC topic. If no real requirement makes its trade-off useful, stop this topic even if it runs correctly and even if the hardware reproduces the scalar speedup.
