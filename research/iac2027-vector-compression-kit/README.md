> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# Bit-exact within-band CCSDS 123 vectorization: physical-test kit

Read the latest `FAIR_REVIEW.md` first, then `METHOD.md`, `PHYSICAL_TESTS.md` and `DECISION.md` before interpreting the results. The latest review is NO-GO for committing to a strong IAC topic on the present evidence; a small physical falsification experiment remains reasonable. Mission necessity and stronger latency comparisons remain unresolved. This is a narrow research prototype, not flight software or a full-standard conformance product.

## Contents

- `src/`: C scalar, AVX2 and actual RVV implementations; build/test scripts; small reference fixtures; self-contained Renode test ELFs.
- `band_matrix/`: one-, two-, three-, four- and eight-band Pavia fixture subsets.
- `large/`: a 256×256×8 Pavia crop.
- `evidence/`: measured host records, reference/provenance metadata, sanitizer results, Renode logs and functional results. No physical board timing or energy results.
- `SOURCES.md`: primary literature and data attribution.

There are 48 native fixture cases, not 48 independent scenes. The real image sources are processed Indian Pines, Pavia University and Salinas acquisitions. First-band subsets and crops do not turn hyperspectral source data into independently acquired multispectral mission data. Salinas is shifted by +11 to fit this unsigned16 profile; that transform is explicit.

## Quick host check

On an AVX2-capable x86 Linux host with GCC:

```sh
python3 src/build.py host
python3 src/run_suite.py --repeats 0 --out results-host-validation
```

The kernel self-test also runs during the host build. See the physical protocol for RVV Linux execution. Compiler/ISA availability is platform-specific; the supplied build was tested with GCC13 and Clang18.

## Renode reproduction

Use Renode 1.17 with RVV support and Clang18/LLVM's RISC-V-capable linker:

```sh
python3 src/build.py rvv --lld /absolute/path/to/ld.lld --renode /absolute/path/to/renode
```

The script creates monitor files and expected-image embeddings with paths for the local checkout. It runs the same ELF at four vector register sizes. Full tests receive 24 seconds of virtual execution to finish. A prior eight-second run stopped before completion with zero mismatches; it was not counted as a pass. Virtual MIPS/time are not hardware performance or WCET measurements.

## Optional fixture regeneration

Supplied fixtures are sufficient for board correctness testing. To obtain the exact public inputs and pinned independent reference model:

```sh
python3 src/fetch_inputs.py
python3 -m pip install -r src/requirements-reference.txt
python3 src/make_frame.py
```

This downloads data into `data/` and the reference into `reference/`. Override `CCSDS_DATA_ROOT` and `CCSDS_REFERENCE_ROOT` if needed. The reference is not modified by this research. `src/make_extra.py` regenerates the band-count and larger-crop cases after those inputs are present.

`SHA256SUMS` records the supplied files. `sha256sum -c SHA256SUMS` checks them before rebuilding. Generated local results and rebuilt binaries will naturally have new hashes.

## Variant identifiers

| ID | Implementation |
|---|---|
| 0 | Specialized fused scalar |
| 1 | Staged scalar |
| 2 | Proposed within-band block speculation |
| 3 | Conventional inter-band SIMD |
| 4 | Calibrated fixed-weight configuration; different predictor parameters |
| 5 | Eager computation of both update signs |

Host timing records are exploratory measurements on an i7-12700H. Reference headers are supplied by fixtures; compressed bodies are checked. Preserve this distinction in any paper.

Third-party materials retain their own terms. Scientific papers, vendor compressor sources and Linux runtime libraries are linked or obtained through the optional setup, not bundled. Do not submit this kit or its AI-assisted report as an IAC paper without resolving the policy issue explained in the decision report.
