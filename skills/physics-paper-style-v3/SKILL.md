---
name: physics-paper-style-v3
description: Organize or revise English theoretical-physics research papers using source-traceable argument planning and local prose operations. Use for whole-paper logic, result presentation, assumptions and scientific interpretation while preserving the supplied physics.
---

Use the user's scientific material, requested length and intended reader as the authority. PhysWhen v3 adds exploratory whole-paper organization to the earlier local operations. Historical examples establish possible organizations, not ideal human writing or a proven readability benefit.

## Choose the scope

For a copy edit or isolated paragraph, use only the relevant local operation below. For a whole draft, outline or authorized structural revision, inspect the supplied question, results, evidence and necessary conditions before choosing sections. Respect a journal's required organization. Do not turn a short request into a full-paper planning exercise.

## Organize the argument when needed

**G1 — Align the paper's promise with what it establishes.** Identify the central question or comparison and the supplied claims that answer it. Distinguish a result from a proposed mechanism, a consistency check and an open problem. An introduction can state the answer early; its promise must retain the restrictions that matter. At the end, return to the question at the strength actually supported. A partial answer or explicitly open question can be the correct ending. Skip another summary when the final analysis already performs this job.

**G2 — Organize around dependencies and branches.** Work out which assumptions, definitions, methods or earlier results are needed for the central claims. Use this to choose a reading route, not to impose one section per item. A result-first overview followed by derivation is legitimate; so is a derivation-led route. If regimes or mechanisms have different assumptions or conclusions, give the reader a recognizable branch point and compare them where their relation matters. Keep conditions recoverable at the claim, including when support appears later. Do not invent a missing proof or use a transition word to conceal it. If information is missing, narrow the claim, identify the gap separately, or leave an explicitly authorized placeholder.

**G3 — Distinguish preview, development and return.** A preview says what the reader is about to learn; the development supplies the actual reasoning or evidence; a later return should help compare, interpret or delimit it. Consolidate repetition that adds none of these functions. Do not remove a useful recap merely because its claim appeared before. Section titles, paragraph counts and a uniform introduction–methods–results template cannot substitute for this decision.

**G4 — Allocate space to the reasoning that matters.** Keep the main claim’s assumptions and logical bridge recoverable on the main reading path. Give a nontrivial transition enough explanation; do not expand an already transparent algebraic step to meet a prose quota. A full technical proof, including one central to the result, may be placed in an appendix when scope allows: retain its role, principal steps, result and necessary conditions in the body, with an accurate pointer. Routine auxiliary derivations can also be grouped or deferred. Never hide a missing argument in an appendix or claim that an unwritten appendix contains proof. Section length need not be equal. An existing discussion can contain a new calculation; its heading alone does not make it a recap.

For an unfamiliar organizational choice, consult [references/structure-evidence.md](references/structure-evidence.md). It describes observed routes and counterexamples with source anchors. These four operations are candidate design choices, not four empirically established improvements.

## Keep local passages useful

- Give a nontrivial display a task if its purpose is otherwise unclear. Skip extra lead-ins for short definitions, already motivated relations and transparent consecutive algebra.
- Where needed, make a central result usable with a supplied consequence, physical reading, subsequent use or scope statement. Do not translate the equation mechanically into a redundant sentence. Several equations can share an explanation.
- Keep the actual condition with the claim it limits. Preserve a simulation's domain, approximation or conditional bound; do not replace it with vague hedging or add uncertainty to imitate a style.

Motivation connects the supplied problem to its question; setup makes needed variables and assumptions recoverable; derivation preserves the dependency; interpretation preserves scope. Mixed paragraphs are legitimate. The earlier local evidence and its separate denominators are summarized in [references/local-evidence.md](references/local-evidence.md).

## Preserve the scientific contract

Preserve supplied equations, signs, units, numerical values, variable meanings, negations, necessary conditions and quantifier scope unless a scientific change is requested. Identify conflicting supplied statements rather than silently choosing one. Use authorized citations; do not invent novelty claims, literature gaps, results or source quotations. Author-presented support in an example is not independent validation of its physics.

Return the requested prose or outline. Keep the planning ledger internal unless requested or needed to expose a material gap. The optional [scripts/check_outline.py](scripts/check_outline.py) checks a supplied outline ledger's references and coverage, not the validity of an argument. Its JSON contract and invocation are in [references/outline-contract.md](references/outline-contract.md). No ledger is required for ordinary writing.

[profile.json](profile.json) reports corpus and annotation denominators separately. Descriptive lengths or section shares are neither optimal targets nor per-paragraph quotas. Do not tune a short excerpt to a whole-paper median. Never output an AI-authorship probability, a single human-likeness score or a claim of improved understanding merely because an organization occurs in historical papers.
