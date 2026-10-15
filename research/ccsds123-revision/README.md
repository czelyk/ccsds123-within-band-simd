> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# CCSDS 123 revision — English working record

15 October 2026. Status: **REVISE**. Read `Research-Revision.md` for the scientific interpretation and `PHYSICAL-PILOT.md` for the target prototype's exact scope. This directory adds evidence and conventional baselines; it preserves the earlier method and historical results.

The revised question is whether exact within-band SIMD offers a useful cost point when spectral parallelism is genuinely limited. This is an algorithm-engineering candidate, not an established highly original mathematical result or a generic spacecraft compression advantage.

## Evidence

- Four actual Landsat 8 Level 1-calibrated products, all seven supplied bands and full 4096x4096 dimensions, selected by the earliest four acquisition dates before inspecting values/results. One training acquisition and three held-out acquisitions. These are processed products; the raw binary container does not make them raw focal-plane data. The publisher keeps OLI bands 1–7 and omits 8/9; no seven-channel instrument or operational constraint is inferred.
- Publisher DOI: https://doi.org/10.34810/DATA1514 ; author Sebastia Mijares i Verdu,2024, dataset V1, CC0. `evidence/landsat8-selection.json` records the deterministic selection; `landsat8-publisher-checksums.json` and `landsat8-downloads.json` retain publisher MD5/local SHA256. All four MD5 values matched.
- `evidence/landsat-pilot.jsonl` retains 189 adaptive timing trials,96 fixed-weight trials,14 independent-reference prefix checks, full-image reference hashes and 24 independent-stripe reset cases. Frequency was not locked. Background data downloading/checksum activity overlapped early cases; no other timing job or Renode validation overlapped those timings. See `environment-notes.json`. Treat times as exploratory host medians.
- `evidence/fixed12-followup.jsonl` records the stronger profile-specific fixed baseline: exhaustive scalar update-bound check, six independent-reference prefix checks, nine default-body identities and 42 calibrated timing trials. It ran after the main campaign and downloads; do not infer paired timing differences across campaigns.
- `evidence/rvv-validation.json` records the revised conventional RVV baselines at VLEN 128/256/512/1024. Per width:144 synthetic cases,2016 method checks and 4,249,224 mapped-residual comparisons, no mismatch. Long cases actually reach both adaptation exponent caps. This is differential functional validation, not physical timing or full-standard certification.
- `evidence/initial-rvv-validation/` preserves the earlier 120-case checks before baseline resource corrections. `evidence/fixed12-initial-check/` preserves the failed validation assertion; `fixed12-check-diagnosis.json` identifies the unused first-sample storage error. Do not run historical drivers as current entry points.
- `evidence/revision-analysis.json`, `fixed12-analysis.json` and `landsat-summary.csv` are derived from the raw records. The original 32 reference source hashes remain unchanged; see `evidence/source-preservation.json` and `original-source-manifest.json`.

The new seven-band pilot favors existing spectral SIMD in all eight main configurations. Independent stripes sometimes improve size; their parallel execution has not been implemented/timed. The Ω=12 option gives almost the same, slightly larger calibrated outputs than Ω=11 here. Keep these negative results.

## Reproduction

Use a separate extracted copy: experiment drivers write their own output files. Actual environment: Python 3.12.3, NumPy 2.5.4, bitarray 3.12.2, Clang 18. `requirements-measured.txt` records package versions. The unchanged external NTNU verification model is required at commit `9fabb0371ebf93d72a0f83ca053e9cdb2c63e3c6` from https://github.com/NTNU-SmallSat-Lab/ccsds123_issue_2_verification_model . Set `CCSDS_NTNU_DIR` to that checkout.

Set `LANDSAT_DATA_DIR` to a data directory with approximately 940 MB free for the four downloaded products. `CCSDS_CPU` selects an available Linux affinity core; the measurement default was 2. Run the host steps sequentially, without other measurement jobs:

```text
python3 fetch_landsat.py
python3 build_host_pilot.py
python3 run_landsat_pilot.py
python3 fixed12_followup.py
```

The independent Python model is slow; full-image harnesses also reserve large output/reference buffers. They are not flight RAM estimates. The BSQ-to-BIP transpose, allocation, file I/O, independent checks, headers and telemetry/DMA are excluded from timing. Training comparisons are retrospective; acquisition ordering does not prove that calibrated products or learned tables were available in flight.

For the bare-metal RVV checks, set `LLD` to a RISC-V-capable LLVM linker and `RENODE` to Renode 1.17, then run:

```text
python3 build_revision.py
python3 run_renode.py
python3 analyze_revision.py
```

Keep Renode separate from host timing. The bare-metal test ELF SHA256 is `74318ec2e71bcf57228958283b1896127e6b66e0a38595e83ae616b8a1fa5271`. `build/linux-build-manifest.json` records the separate Linux cross-build, which has not run on a physical target. See `PHYSICAL-PILOT.md` before using it. The generated normal harness and validation-only capture harness are separate; do not time the latter.

`export_input.py` converts a delivered u16le BSQ product to BIP/BIL for the target prototype without changing values and writes provenance. Exporting does not create a real sensor arrival trace.

The archive excludes the approximately 940 MB inputs, external runtimes/toolchains/reference checkout, downloaded third-party full papers, and the earlier historical kit. Dataset retrieval and source links remain available in the package. This prototype does not complete the raw-workload, strongest-target-baseline, physical-performance or IAF-policy gates.

## Scope and policy

The official CCSDS raw D8 Landsat/D10 Vegetation corpus could not be accessed here (403). Do not replace those actual profiles with D16 padding. The NASA-hosted 2025 LandIS paper is relevant per-band context but uses near-lossless/hybrid compression and FPGA development, outside this prototype's qualified profile. Access records and primary links are retained.

`IAF-clarification-draft.md` accurately describes AI assistance for human review. It has not been sent. IAF eligibility remains unresolved under the actual 2027 Call for Papers; no acceptance guarantee or probability is given.
