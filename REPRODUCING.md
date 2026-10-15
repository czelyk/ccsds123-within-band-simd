# Reproduction

Run commands from the repository root. Use `scripts/reproduce.py` to prepare a fresh ignored copy under `runs/`. Existing evidence must not be overwritten. None of the commands below publishes a repository, contacts a researcher, or starts a physical-board test.

## Integrity

```sh
python3 scripts/check_repository.py
```

This checks the public file manifest and all32 original reference-source hashes in all three preserved source copies, parses active Python/JSON records and checks primary documentation links. The original campaign manifests and SHA256SUMS remain historical provenance. They include files omitted from the public package and pre-redaction log hashes; do not substitute them for the public manifest.

## Host smoke check

Requirements: Python3.10+, Linux/x86-64 with AVX2 and GCC. No Python scientific packages, external model or dataset download is required.

```sh
python3 scripts/reproduce.py host-smoke
```

This builds the original native program, runs its kernel oracle/arithmetic check, then validates six included synthetic full-compressor fixtures with zero timing repetitions. These six fixtures are not the complete historical48-case fixture collection. Real-image fixture measurements remain archived; their input-derived binaries are regenerated separately if desired. A smoke pass is not independent full-standard conformance.

## Stronger host regression

Requirements: Clang18 on Linux/x86-64 with AVX2 and AddressSanitizer/UndefinedBehaviorSanitizer runtimes.

```sh
python3 scripts/reproduce.py sanitizer-check
```

The existing reassessment driver runs its synthetic differential regression and retains the new result in the run copy. This is an implementation portability check, not a new performance experiment or scientific dataset.

## Revised RVV correctness build

Requirements: Clang18 and a RISC-V-capable LLVM linker. The build is bare-metal rv64gcv_zba_zbb, lp64d. Set `LLD` if `ld.lld` is not on PATH.

```sh
LLD=/absolute/path/to/ld.lld python3 scripts/reproduce.py rvv-build
```

The prepared run directory and successful build are printed. To execute the four VLEN functional checks, use Renode1.17 with RVV support:

```sh
RENODE=/absolute/path/to/renode LLD=/absolute/path/to/ld.lld \
  python3 scripts/reproduce.py renode-check
```

The latter prepares another copy, builds, and runs the revised checks at VLEN128/256/512/1024. Its historical expected counts are144 synthetic cases,2016 method comparisons and4,249,224 mapped-residual comparisons per width, with zero mismatches. Long cases reach both adaptation caps. These counts are not numbers of independent scenes. Simulator wall time/virtual time are not physical performance or energy.

The older reassessment-only Renode driver expects an original ELF: first build the original RVV kit in the same prepared tree if reproducing that historical check. Compiled ELFs are intentionally not shipped. The revised check above does not need the original ELF or external image data.

## Full source/evidence reproduction

Prepare the relevant campaign:

```sh
python3 scripts/reproduce.py prepare revision
```

The script prints the new directory. Change into its `research/ccsds123-revision` subdirectory before invoking the existing experiment drivers. Set data and reference variables to absolute paths. The scientific drivers remain research scripts: they may be slow and use several GB of RAM. Set `CCSDS_CPU` to an available affinity core; its historical default2 may not be available on your machine. Keep timing jobs sequential and record the actual clock/thermal/background-load conditions.

### Independent reference

Obtain the unchanged model from [NTNU SmallSat Lab](https://github.com/NTNU-SmallSat-Lab/ccsds123_issue_2_verification_model), commit `9fabb0371ebf93d72a0f83ca053e9cdb2c63e3c6`. Its source is not vendored. Use a separate Python virtual environment and the measured dependency files for the relevant campaign; availability on every Python version/platform is not guaranteed.

```sh
export CCSDS_NTNU_DIR=/absolute/path/to/ccsds123_issue_2_verification_model
export CCSDS_CPU=2
```

### Seven-band Landsat pilot

The [publisher collection](https://doi.org/10.34810/DATA1514) supplies calibrated Level1 u16le BSQ products. The four files and hashes are in `evidence/landsat8-selection.json`, `landsat8-downloads.json` and `landsat8-publisher-checksums.json`. They total approximately940MB. Do not replace them with raw focal-plane products or imply their BSQ-to-BIP replay represents sensor arrival.

In the prepared revision directory, with NumPy/bitarray and the pinned model available:

```sh
export LANDSAT_DATA_DIR=/absolute/path/to/landsat-data
python3 fetch_landsat.py
python3 build_host_pilot.py
python3 run_landsat_pilot.py
python3 fixed12_followup.py
```

Run `analyze_revision.py` after the revision's four Renode validation records are also present. The prepared copy contains historical functional records; its analysis does not prove a fresh local Renode run unless you actually replace them by running it. Similarly, the raw historical measurements are not new local results. Output filenames intentionally follow the original campaign; the run-copy boundary protects the archive.

The first fixedΩ=12 assertion failure is retained under `evidence/fixed12-initial-check/` with its diagnosis. Do not execute that historical failed driver as the current entry point. Its error included unused first-sample storage; no timing trials preceded it.

### HYPSO comparisons

Prepare a reassessment copy:

```sh
python3 scripts/reproduce.py prepare reassessment
```

Use the four NetCDF inputs identified by publisher DOIs and hashes in `selected-hypso-inputs.json`. Place them under `raw/` in a data directory and set `CCSDS_DATA_DIR` to that parent directory. They total approximately394MB. Use the actual `products/dn` arrays without normalization or clipping, retaining their956×684×120 shape and spectral-binning provenance. NumPy, h5py, bitarray and the independent model are required.

In the prepared reassessment directory:

```sh
python3 build_new_baseline.py
python3 build_bip_baseline.py
python3 check_new_baselines.py
python3 run_new_baseline.py
python3 run_bip_baseline.py
python3 analyze_evidence.py
```

Full-cube residual checks compare with specialized C scalar code; independent NTNU checks cover prefixes. The100 older follow-up records, including38 fixed-weight cases, are separate historical measurements. Their `prior-source/` session fragments are retained for provenance, not advertised as standalone portable experiment drivers.

### Original image-derived fixtures

In a prepared original-kit directory, `src/fetch_inputs.py` obtains the attributed inputs and pinned model; install `src/requirements-reference.txt`, then run `src/make_frame.py` and `src/make_extra.py`. Read the dataset terms first. The six synthetic fixtures already included need no download. The small `reference_cases.h` numerical oracle vectors are retained with the original source hashes.

The historical input subsets/crops and explicit Salinas+11 shift must remain described accurately. They are processed airborne acquisitions, not raw spacecraft sensor data. Regenerating omitted fixtures does not create additional independent scenes.

## RVV Linux pilot

The preserved [physical-pilot document](research/ccsds123-revision/PHYSICAL-PILOT.md) describes native and cross-build inputs and exclusions. The public package contains its source, not a precompiled executable. The current scientific recommendation is NO-GO; the existence of this build route is not a recommendation for hardware acquisition or a claim that mission prerequisites are complete.
