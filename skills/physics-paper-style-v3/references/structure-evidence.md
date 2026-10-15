# Whole-paper evidence and limits

The current validated semantic inventory contains 30 discovery papers, 1349 parsed main-body paragraphs and 134946 prose words actually read, with 539 selected nodes and 537 selected edges. Figures, appendices and parser-boundary limitations are recorded individually in the project report. These are host-agent judgments, not human gold labels.

Initial selection:12 papers, one per three categories × four year bands,800–12000parsedprosewords, prior local-window papers excluded. A second12-paper stage uses the second rank under the same seed/eligibility per stratum, selected after initial auditing; this is further discovery, not heldout confirmation. A subsequent6-paper newly acquired cohort is listed separately in profile.json. Selected graph nodes and recurrence pairs are not exhaustive; they cannot estimate whole-corpus prevalence.

Among these maps, 22 papers have at least one selected claim with both preview and development occurrences. Question states: {'answered': 55, 'open': 34, 'uncertain': 1}; edge evidential bases: {'explicit': 479, 'inferred': 58}. These describe annotations, not readability benefits.

| Candidate operation | Source-located observation | Inference boundary |
|---|---|---|
| G1 | 1602.05065, node c7: An initially motivated viability question can end in a negative conclusion. | An observed option/counterexample; no causal benefit established. |
| G1 | 1909.00580, node l1: An observational fit alone does not establish the proposed mechanism. | An observed option/counterexample; no causal benefit established. |
| G2 | 1004.3611, node c1: The linear alignment branch has a restricted rescaling result. | An observed option/counterexample; no causal benefit established. |
| G2 | 1004.3611, node c2: The quadratic branch has a different distinguishability result. | An observed option/counterexample; no causal benefit established. |
| G3 | 1405.2215, node c3: A result is previewed, developed under its energy bound and later recapped. | An observed option/counterexample; no causal benefit established. |
| G3 | 2007.04256, node ev1: A robustness argument follows use of an approximation; this is not automatically an ordering defect. | An observed option/counterexample; no causal benefit established. |
| G4 | 1007.0970, node c6: A final interpretation can occur without a separate conclusion section. | An observed option/counterexample; no causal benefit established. |
| G4 | 1004.3611, node c5: A discussion can still contain a new mitigation calculation. | An observed option/counterexample; no causal benefit established. |

Read [structure-source-anchors.jsonl](structure-source-anchors.jsonl) for exact versions, hashes, paragraphs and raw source-line containers. Underlying exact fragments were checked against comment-stripped raw source and remain in the local evidence cache; the portable index contains organizational paraphrases and quote hashes. Container line spans are not exact token-level coordinates. The paper authors’ scientific claims are not independently endorsed.

G1–G4 are engineering hypotheses derived from these observations and argument-traceability requirements. In particular, allocating explanatory space and choosing an appendix are design judgments; no historical frequency proves the optimal placement. There is no prescribed section count, relative length or dependency-order score.

Automatic corpus measurements only supply section/label/reference navigation and frozen D01–D06 distributions. They cannot extract logical support by themselves. The learned distinction is between presentation order and logical dependence: a preview may legitimately precede the support required to assess it.

Independent source review and writing-task validation are documented in the project release report. Even successful execution does not demonstrate reader preference. Existing v1/v2 blind-study outputs remain frozen and cannot establish a v3 effect.
