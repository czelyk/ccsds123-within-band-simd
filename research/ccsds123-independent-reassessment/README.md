# Historical independent reassessment

This preserved campaign added component SIMD, native-BIP spectral execution, synthetic sanitizer checks, residual/state comparisons and trace analysis. It originally supported REVISE. **The current project recommendation is NO-GO**, as explained in the [final assessment](../ccsds123-final-feasibility/Final-Feasibility.md).

Use the root [REPRODUCING.md](../../REPRODUCING.md) for portable commands. `src/`, `evidence/`, `selected-hypso-inputs.json` and `prior-followup-records.json` retain the implementation, raw positive/negative records and input provenance. The historical100 follow-up records include38 fixed-weight cases. Older full diagnostic arrays that existed only in memory were not recovered; the new `trace-*.npz` arrays are separate retained measurements.

Independent NTNU checks cover prefixes. Complete-cube new residual comparisons use the specialized C scalar reference. Host timings are exploratory i7-12700H measurements with uncontrolled frequency; they are not physical RVV performance. The original32 reference files remain unchanged in `src/reference_kernels/`.

Historical manifests/logs describe the pre-publication archive; see root [PACKAGING.md](../../PACKAGING.md) for redactions, omitted data/publication files, generated binary exclusions and public-package hashes. The duplicate historical Turkish narrative was not copied into this English package; all numerical evidence and the English final assessment are preserved.
