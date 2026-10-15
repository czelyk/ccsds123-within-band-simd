# Attribution and external materials

The code implements a restricted profile of the [CCSDS123 compression standard](https://ccsds.org/Pubs/123x0b2e2c3.pdf). The CCSDS standard and its name are not authored by this project. The standard, full publication texts, external compressor/model source, toolchains and external input datasets are not redistributed here.

## Independent model and numerical vectors

[NTNU SmallSat Lab's CCSDS123 Issue2 verification model](https://github.com/NTNU-SmallSat-Lab/ccsds123_issue_2_verification_model), commit `9fabb0371ebf93d72a0f83ca053e9cdb2c63e3c6`, provided independent prefix/oracle checks. Attribution: Vorhaug, Boyle and Orlandić, *High-Level CCSDS123.0-B-2 Hyperspectral Image Compressor Verification Model*, WHISPERS2024. Obtain the model separately and retain its own notices/terms.

`reference_cases.h` contains small numerical test vectors/expected outputs used in the original kernel checks. The six included `frame_constant_*`, `frame_checkerboard_*` and `frame_noise_*` binaries contain synthetic input plus reference-generated expected compressed data/header bytes. These are generated research fixtures, not a vendored copy of the model. Independent model checks in this project are limited in scope and do not inherit the model authors' complete verification campaign.

## Data provenance

- [HYPSO collection](https://doi.org/10.18710/ZR0MVS): selected file DOIs, publisher MD5 and retained local SHA256 appear in the reassessment metadata. Inputs are L1A binned DN. Publisher access conditions remain applicable; no full NetCDF files are shipped.
- [CORA Landsat8 collection](https://doi.org/10.34810/DATA1514), Sebastià Mijares i Verdú,2024: calibrated Level1 seven-band products, with file selection and publisher/local checksums in the revision metadata. The recorded collection is CC0; no approximately940MB source files are shipped.
- Indian Pines, Pavia University and Salinas: processed AVIRIS/ROSIS acquisitions obtained through the [HybridSN authors' data repository](https://github.com/gokriznastic/HybridSN/tree/master/data). Provider and research-paper attribution, URLs and hashes appear in the original kit's SOURCES/provenance. Availability in a mirror is not a new license grant by this project. Full source files and real-image-derived frame binaries are excluded; the retained small numerical kernel vectors were generated during the research checks.

## Related work and tools

See the original [primary source list](research/iac2027-vector-compression-kit/SOURCES.md) and final [application source ledger](research/ccsds123-final-feasibility/source-ledger.md). Prior exact block filtering, guarded speculation, CCSDS dependency reduction, update bypass, spectral SIMD and independent contexts are not attributed to this project.

Renode, GCC, LLVM/Clang, Python and scientific Python libraries retain their authors' licenses. They are prerequisites, not bundled project components. No upstream author or space agency is represented as endorsing this implementation or its conclusions.
