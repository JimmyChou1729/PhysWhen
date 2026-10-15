# Evidence and operating limits

This is the frozen local-evidence record underlying v2 operations, retained for v3. Its reference corpus had 210 usable historical English theoretical-physics papers. Only the 168 discovery papers supply reference distributions and rule-development evidence; 42 remain held out.

## What was actually examined

- Initial sample:15 discovery papers,60 formula-centered windows,360 labels;59 main-body windows and1 appendix window. This evidence produced the frozen first skill.
- Additional sample:12 different discovery papers,60 windows,360 labels, category/year-band stratification with five role-preferred targets per paper.26 targets contain a display and34 are prose-only. The selected section labels are13 introduction,9 discussion/conclusion,38 technical body. Local neighboring paragraphs may overlap.
- Combined inventory:27 papers,120 windows,720 labels. This is an inventory total, not a pooled prevalence denominator. The added sample deliberately broadens paragraph functions.

All six features were assigned by host agents who read the supplied source contexts. Exact quotations, version identity, line ranges and frozen contexts are machine-validated; quotations/full source stay in the local project cache. These are not human gold labels. The sample is not evidence that a strategy improves reading.

| Feature | Additional-window labels | Applicable yes/no papers |
|---|---|---:|
| S01 | {'motivation': 10, 'mixed': 7, 'derivation': 13, 'interpretation': 13, 'setup_definition': 12, 'limitation': 3, 'transition': 2} | N/A |
| S02 | {'not_applicable': 34, 'yes': 25, 'no': 1} | 12 |
| S03 | {'not_applicable': 34, 'yes': 26} | 12 |
| S04 | {'yes': 28, 'no': 21, 'uncertain': 11} | 12 |
| S05 | {'no': 5, 'yes': 55} | 12 |
| S06 | {'yes': 57, 'not_applicable': 2, 'uncertain': 1} | 12 |

S01 records the target paragraph function. S02 asks whether purpose is stated before the target display, S03 asks about meaning/use/scope after it; both are NA for prose-only targets. S04 records timing for one identified local item. S05 concerns an identified transition in the supplied window; S06 an identified principal claim and its conditions. They do not establish scientific correctness or global novelty.

The20-window independent audit compared120 judgments, with107 original exact matches and13 disagreements.32 S02/S03 NA matches inflate the pooled figure; selected-item differences also affect S04. This is diagnostic agreement with an independent agent, not accuracy or a human reliability result. Original judgments are preserved. Parent adjudication marks two newness cases and one principal-claim case uncertain, marks two role-boundary cases mixed, and replaces one equation-use evidence quote.

## How this changes writing decisions

| Decision | Observation basis | Boundary |
|---|---|---|
| R1: clarify a nontrivial display’s task | S02 in26 applicable added targets across12 papers | Optional; observed presence is not evidence that every equation needs a preamble. |
| R2: make a central result usable | S03 in26 applicable added targets across12 papers | A symbol-definition clause is not automatically an interpretation; a mathematical subsequent use can qualify. |
| R3: preserve claim conditions | S06 across60 added mixed windows | Source-backed scope only; no invented hedges or universal claim expansion. |
| Route by paragraph function | S01: motivation/setup/derivation/interpretation all represented | Functional routing is a project design decision; sparse classes are not universal templates. |
| Do not mechanically move all definitions before displays | S04 has28 yes,21 no,11 uncertain | The strict timing label is not a quality judgment; after-equation definitions may be appropriate. |
| Flag a missing reasoning bridge | S05 includes5 locally unsupported cases | Do not infer complete-paper absence, fabricate a proof, or demand every intermediate step. |

See local-source-anchors.jsonl for located supporting and contrasting observations. They are paraphrases of organization plus source coordinates, not prose to imitate. One sampled source has internally inconsistent formulas; those formulas are excluded from the anchors. Another adjacent context contains acknowledgments; it is not used as scientific evidence.

## Reference measurements

| Per-paper measure, then across discovery papers | n | Median | Q25–Q75 |
|---|---:|---:|---:|
| D01_sentence_median | 168 | 21.000 | 19.000–23.000 |
| D02_paragraph_median | 168 | 94.500 | 76.375–113.250 |
| D03_display_per_1000_words | 168 | 11.657 | 7.022–16.295 |
| D04_before_median | 168 | 19.000 | 14.500–23.625 |
| D04_after_median | 168 | 20.000 | 15.000–24.000 |

Words are English prose tokens excluding recognized math/citations. The full source parser and the portable plain-text helper differ; whole-paper distributions do not calibrate a short excerpt. D03 counts display environments, and D04 looks at up to two nearby prose sentences within a section; adjacent math may give zero, boundaries may be missing. Do not optimize toward these values.

## Validation status

Skill format and independent forward execution are checked separately in the project release report. Earlier group experiments used frozen v1/v2; neither validates the new structural operations. No human effect, AI-authorship probability, or trained weight model is claimed.
