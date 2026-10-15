# CCSDS 123 within-band SIMD

Research implementation and reproducibility archive for an exact within-band SIMD execution method for a restricted lossless CCSDS 123 profile. Includes scalar, AVX2 and RISC-V Vector implementations, conventional comparators, host measurements, Renode correctness evidence and critical assessments.

**Research status: NO-GO for advancing the current claim as the intended IAC 2027 paper.** The final application audit did not substantiate a distinctive spacecraft benefit after the applicable alternatives. The code and both favorable and unfavorable results are preserved as a research record. This is a prototype, not flight-qualified software or a complete CCSDS conformance product. No physical RVV performance or energy results are available.

## Findings

- The proposed execution transformation preserves adaptive integer states when its verification succeeds, and replays rejected blocks with the scalar recurrence.
- It beat the best tested sequential/single-band host path by 1.230–1.366x in the seven-band pilot.
- Conventional adaptive spectral SIMD was faster in all eight main seven-band configurations, using approximately 9–17% less host time at the same compressed size. Four acquisitions with two settings are eight configurations, not eight independent scenes.
- Independent-context reset costs and calibrated fixed-weight comparisons are retained, including cases unfavorable to the proposed framing. Parallel independent-context performance was not measured.
- The revised Renode checks passed at VLEN128/256/512/1024, with 2016 method checks per width. These are functional checks, not physical throughput, energy, WCET or independent full-standard certification.

Read the [final feasibility assessment](research/ccsds123-final-feasibility/Final-Feasibility.md) for the decision, evidence and remaining uncertainties. The assessment is AI-assisted analysis, not external independent human peer review. There is no claim of verified high mathematical originality or predicted conference acceptance.

## Start here

```sh
python3 scripts/check_repository.py
python3 scripts/reproduce.py host-smoke
```

The first command needs only Python3.10+. The second needs Linux/x86-64 with AVX2 and GCC. It builds and validates the original kernel and six synthetic full-compressor fixtures in a fresh ignored `runs/` directory, with no timing campaign and no data downloads. The included tiny numerical oracle vectors are generated research test data; see [third-party attribution](THIRD_PARTY.md).

Use [REPRODUCING.md](REPRODUCING.md) for sanitizer checks, the revised RVV build, Renode and full dataset experiments. All new runs use disposable copies so they cannot overwrite the archived evidence.

## Repository map

| Location | Purpose |
|---|---|
| [docs/METHOD.md](docs/METHOD.md) | Current method, correctness conditions and limitations |
| [research/iac2027-vector-compression-kit](research/iac2027-vector-compression-kit) | Original implementation, synthetic fixtures, initial measurements and historical reviews |
| [research/ccsds123-independent-reassessment](research/ccsds123-independent-reassessment) | Stronger component/native-BIP comparisons, complete historical records and trace arrays |
| [research/ccsds123-revision](research/ccsds123-revision) | Latest conventional RVV baselines, seven-band pilot, fixed-weight follow-up and failed-check diagnosis |
| [research/ccsds123-final-feasibility](research/ccsds123-final-feasibility) | Bounded mission/application audit and final NO-GO decision |
| [provenance](provenance) | Selection, source hashes, redactions, exclusions and portable driver edits |
| [FILE_MANIFEST.json](FILE_MANIFEST.json) | Hashes for this public source/evidence snapshot |

Historical reports retain the decisions and limitations applicable when they were written. REVISE or physical-pilot text in those reports does not supersede the final NO-GO recommendation. Historical source trees are intentionally kept together to preserve experiment identity; they are not independent libraries or additional candidate topics.

## Scope and data

The current method covers unsigned16, lossless zero damping/offsets, Ω=19/R64/P3, full prediction, two local sums and sample-adaptive entropy coding, with blocks capped at eight samples. A particular profile, ISA or preserved output ordering is an experimental choice, not a mission requirement. Conventional BIP output interleaving is allowed in the comparisons.

Full external datasets, image-derived frame files, third-party compressor/model sources, publication PDFs/full texts, toolchains and compiled executables are excluded. Data sources, hashes, selections and optional regeneration scripts are included. The Landsat pilot uses calibrated Level1 products; HYPSO inputs are uncalibrated, spectrally binned DN. Neither is relabeled as an unbinned native-camera stream.

[PACKAGING.md](PACKAGING.md) explains public-package differences from the original local archives. Those archives were left unchanged. File paths and workstation identifiers were redacted from public logs without altering the numerical measurement fields.

## Attribution, license and citation

See [THIRD_PARTY.md](THIRD_PARTY.md), [LICENSING.md](LICENSING.md) and [CITING.md](CITING.md). No software license has been selected for the original project materials; this repository is not currently an open-source license grant. Public visibility must not be confused with permission to reuse third-party data or code.

AI assistance was used for implementation, experiments, literature investigation and scientific assessments. The records are not a submitted or peer-reviewed paper. Conference policy/eligibility questions are separate from the scientific NO-GO decision.
# ccsds123-within-band-simd
