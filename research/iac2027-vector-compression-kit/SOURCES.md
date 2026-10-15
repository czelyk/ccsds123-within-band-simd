> Historical research snapshot. The current decision is NO-GO. Use the repository root README and REPRODUCING.md for public-package contents and commands; some original data and generated binaries are intentionally omitted.

# Primary sources and attribution

## Closest prior methods

1. Sánchez et al., **Reducing Data Dependencies in the Feedback Loop of the CCSDS 123.0-B-2 Predictor**, IEEE GRSL 2022, DOI [10.1109/LGRS.2022.3213975](https://doi.org/10.1109/LGRS.2022.3213975). [Author copy](https://deic.uab.cat/~jbartrina/docs/articles/2022_10-IEEE_GRSL_IUMA_UAB.pdf). Examined dependency analysis, the sign derivation, eager two-sign weight updates and results. Already establishes bit-identical acceleration.
2. Barrios et al., **Removing Data Dependencies in the CCSDS 123.0-B-2 Predictor Weight Updating**, IEEE GRSL 2024, DOI [10.1109/LGRS.2024.3362376](https://doi.org/10.1109/LGRS.2024.3362376). [Author copy](https://deic.uab.cat/~jbartrina/docs/articles/2024_01-IEEE_GRSL.pdf). Examined the bypass condition, partial updating, exogenous calibration and coding/hardware results. Fixed weights can also improve compression on some data.
3. Papadantonakis et al., **Pipelining Saturated Accumulation**, [FPT 2005 extended paper](https://ic.ese.upenn.edu/pdf/sataccum_icfpt2005_extended.pdf), and [journal work](https://cas.ee.imperial.ac.uk/people/nachiket/publications/sataccum_jrnl.pdf). Saturating accumulation can be reformulated for parallel execution; that mathematical idea is not claimed here.
4. Sun, Gabrielli and Jones, **Speculative Vectorisation with Selective Replay**, ISCA 2021, [author paper](https://www.cl.cam.ac.uk/~tmj32/papers/docs/sun21-isca.pdf). Establishes broader speculative vector execution and replay; its hardware memory-dependence mechanism is not this CCSDS implementation.

## Space compression context

5. [CCSDS 123.0-B-2 with corrigenda](https://ccsds.org/Pubs/123x0b2e2c3.pdf), normative compression algorithm.
6. [CCSDS 120.2-G-2](https://ccsds.org/Pubs/120x2g2.pdf), informational report and representative image corpus. Official test/data downloads were not accessible in this session; no independent claim of passing that full corpus is made.
7. [Versal AI Engines for On-Board Data Compression, OBPDC 2024](https://zenodo.org/records/13863610/files/VersalAIEnginesforOnBoardDataCompressionImplementationandPerformanceAnalysisofCCSDS121andCCSDS123.pdf), established vector processing across bands and complete-pipeline constraints.
8. [Development and Integration of CCSDS 123.0-B-2 FPGA Accelerator for HYPSO-1](https://simenlei.folk.ntnu.no/publications/2024_ESA_Onboard_Compression.pdf), dependency, memory and implementation discussion. Its FPGA throughput is not directly compared to host CPU timings.
9. Ferraz, Silva and Falcão, [Hyperspectral Parallel Image Compression on Edge GPUs](https://www.mdpi.com/2072-4292/13/6/1077), Remote Sensing 2021. [Author implementation](https://github.com/oscarferraz/CCSDS-123). Prior band/tile/heterogeneous parallel compression is not a new contribution here.
10. Kiely et al., [The Emerging Issue-3 Revision, OBPDC 2024](https://ntrs.nasa.gov/api/citations/20240012764/downloads/THE%20EMERGING%20ISSUE-3%20REVISION.pdf). The discussed ROI extension leaves prediction calculations unchanged; it is not evidence that every future revision is covered by this prototype.

## Independent oracle and image data

11. Vorhaug, Boyle and Orlandić, **High-Level CCSDS 123.0-B-2 Hyperspectral Image Compressor Verification Model**, WHISPERS 2024. [Paper](https://ntnuopen.ntnu.no/ntnu-xmlui/bitstream/handle/11250/3180913/WHISPERS_2024_paper_75.pdf?isAllowed=y&sequence=1), [repository](https://github.com/NTNU-SmallSat-Lab/ccsds123_issue_2_verification_model), pinned commit `9fabb0371ebf93d72a0f83ca053e9cdb2c63e3c6`. Its authors' verification campaign is distinct from the checks executed in this project.
12. Roy et al., **HybridSN**, [paper](https://arxiv.org/abs/1902.06701), [author-hosted input data](https://github.com/gokriznastic/HybridSN/tree/master/data). Files used: `Indian_pines_corrected.mat`, `PaviaU.mat`, `Salinas_corrected.mat`. Hashes are in `src/provenance.json`. These are processed airborne image datasets, not raw spacecraft images. Dataset acquisition attributions remain with their original AVIRIS/ROSIS providers.

## Enabling hardware and conference

13. [Microchip PIC64-HPSC](https://www.microchip.com/en-us/products/microprocessors/64-bit-mpus/pic64-hpsc), [series sheet](https://ww1.microchip.com/downloads/aemDocuments/documents/MPU64/ProductDocuments/Brochures/PIC64-HPSC-Series-00005391.pdf). Supports space relevance of vector processors; no performance, compatibility certification or radiation result on this hardware is claimed.
14. [BPI-F3 official documentation](https://docs.banana-pi.org/en/BPI-F3/BananaPi_BPI-F3), documented RVV 1.0 development hardware. This COTS board is not presented as flight-qualified.
15. [Official IAC 2027 call](https://www.iafastro.org/assets/files/events/iac/2027/IAC2027_Call_for_papers.pdf): D1.2 software-technique scope, selection criteria, deadlines and AI-use policy. The AI policy requires explicit clarification for the assistance used in this work before eligibility can be assumed.

The review also examined earlier GPU/CPU optimization literature and an Edinburgh 2017 thesis. Search coverage is finite. Absence from these examined sources is not proof of universal originality.
