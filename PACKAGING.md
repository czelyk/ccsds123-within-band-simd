# Public-package preparation

This directory is a curated copy of the research workspace, prepared15October2026. The original local workspace and all its results were left unchanged. No remote GitHub repository was created or published by this preparation.

## Preserved

- Original scalar/AVX2/RVV kernels and complete compressor harnesses; all32 reference source files remain byte-identical in all three retained copies.
- Revised conventional comparator sources, host/RVV build scripts and experiment drivers.
- Numerical host records, CSV/JSON summaries, compressed trace arrays, source/data hashes and environment qualifications.
- Renode status records/logs and both earlier/final validation evidence.
- The failed fixed-weight assertion, partial records and its diagnosis.
- Historical favorable and unfavorable findings, current English research assessment and final NO-GO application audit.
- Six synthetic image fixtures and small generated numerical oracle vectors. The external reference implementation is not included.

## Deliberately omitted

- Full source imagery, large NetCDF/raw/MAT datasets and real-image-derived frame binaries. The files, selections, download/regeneration routes and hashes remain documented.
- Third-party full-text papers, standards, conference calls and downloaded website/session pages. Links and the source ledger remain. Historical references to local paper copies refer to the original research archive, not included public files.
- Compiled executables, libraries, object files and generated monitor scripts containing workstation-specific paths. Build sources and historical compiler manifests/logs remain.
- Unsent correspondence, duplicated historical non-English narrative and redundant historical rendered figures. English assessments, all numerical records and plotting source remain. These exclusions do not remove negative measurements.
- Toolchains, virtual environments, model checkouts, chat histories, attachments and unrelated topic research.

## Redaction and portability

Personal absolute home/workspace paths and the original workstation hostname were replaced in public logs/metadata. Three CRLF text/CSV files were normalized to LF so Git checkout preserves the public checksums. Numerical timing, byte counts, validation outcomes, dataset hashes and scientific parameters were not changed. Redacted/normalized files are copies, not the original byte streams; their public hashes naturally differ. The initial clean-export checksum failure and its diagnosis are retained under `provenance/packaging-checks/`.

Eight active Python drivers now discover tools using environment variables/PATH and use portable data/reference defaults. Missing Landsat inputs fail promptly instead of waiting for a background downloader. No C algorithm or benchmark selection was changed. [driver-changes.json](provenance/driver-changes.json) records those edits.

[packaging.json](provenance/packaging.json) records source/destination hashes, selections, exclusions and initial redactions. Its initial `public_sha256` fields precede later documented driver edits and documentation banners. The final [FILE_MANIFEST.json](FILE_MANIFEST.json) is authoritative for this public snapshot.

Original `artifact-manifest.json` and `SHA256SUMS` files inside historical campaigns remain records of the earlier complete archives, including omitted files and unredacted logs. They cannot verify the public snapshot. The final application audit's statement that128 revision files and102 reassessment files matched describes the original audit, before public packaging.

Reproduction uses fresh ignored copies under `runs/`. Source and evidence files under `research/` are an archive; avoid running mutating experiment drivers there directly. Existing source-hash assertions remain enabled.
