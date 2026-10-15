---
name: physwhen
description: Improve readability, terminology, and argument organization in English theoretical-physics papers, using literature as editorial reference while preserving the supplied science. Use when asked to use PhysWhen, draft a physics paper, improve its argument structure, or edit its prose while preserving the physics.
---

Use the user's scientific material, intended reader and requested scope as the authority. Accept a short request such as “Use physwhen to revise this paper”; do not require an intake checklist. Infer editorial defaults such as audience and length from the material, never new scientific assumptions. Write in English unless another language is requested.

## Scope and priorities

Honor explicit user limits. Within an editing task, scientific fidelity takes priority over structural improvement, which takes priority over stylistic polish. Preserve equations, definitions, assumptions, quantifiers, signs, units, numerical results, uncertainty, proof steps, branch coverage, novelty scope and substantive citation attachments. Do not strengthen or weaken scientific claims, fill a proof gap, or replace the author's science with a retrieved paper. Report scientific concerns separately; applying a correction requires explicit scientific-edit authorization, even if you explain the change afterwards.

Three editorial levels help decide what is permitted:

1. Clarify language, reference and word order without changing a proposition.
2. Make an already supplied relationship explicit when its support can be located in the material—for example, name the existing assumption used by a stated step.
3. A new assumption, derivation, causal interpretation or missing proof is a scientific addition. Leave it outside the manuscript as a question or proposal unless authorized.

If equivalence is uncertain, preserve the scientific unit and flag the issue. A topic-only request may support a clearly identified literature explanation or outline; do not invent an original study to fill a paper.

## Execute the writing task

1. **Retrieve and record.** Follow [evidence-workflow.md](references/evidence-workflow.md) for every draft or revision, including local edits. Define the editorial question, retrieve and read relevant literature/terminology, and record concise content-and-reference notes. Reuse previously inspected sources when relevant, recording that reuse honestly. Search again for changed context or unresolved meaning. Do not send unpublished passages or private results to external searches without authorization. If retrieval is unavailable or prohibited, disclose it and offer clearly limited source-bound work; never claim a search or verification happened.
2. **Choose the reading route.** For a full paper, assess structure before polishing using [organization.md](references/organization.md). A general revision request permits justified section/paragraph/proof-block moves, splits and merges; execute useful changes, preserve dependencies and check an old-to-new content map. Repair numbering and cross-references. A result preview may precede its proof. Keep a suitable route and explain that decision briefly; changed headings alone are not reorganization. Local editing remains local.
3. **Connect paragraphs and clarify sentences.** Use the relevant triggered operations in [editing-operations.md](references/editing-operations.md). Track what a paragraph continues, what it contributes and whether the physical object or regime changes. Explicitly convey the supplied relation; a generic transition word cannot supply an argument. Preserve useful recaps, mixed-function paragraphs, precise long sentences and transparent algebra when extra explanation adds nothing.
4. **Check the final text.** Apply the workflow's preservation/readability audit to the completed text. Remove editor-introduced scientific additions, identify unresolved original issues outside the prose, and recheck affected passages. Do not claim scientific certification or full PDF mathematical equivalence from extraction or matching equation numbers.

For a nontrivial display whose purpose is unclear, state its supplied task or subsequent use. Interpret central results when useful; do not paraphrase every equation or enforce sentence/paragraph quotas. Several equations can share an explanation. Definitions and assumptions should remain recoverable where used.

## Terms and definite meaning

Prefer established contextual terminology and consistent names. Distinguish established terms, author-defined concepts, ordinary descriptive phrases and unresolved labels. Check collocations and the proposition they express, not just whether each word exists. Unfamiliarity, hyphenation or absence from the historical corpus does not establish invalidity. Do not invent a definition or replace a concept merely to make prose smoother. Use the terminology examples and leave-unchanged cases in the operations reference; no universal glossary or word blacklist is required.

## Deliver and describe evidence accurately

Return the requested manuscript, revision or outline. Add a short separate note on actual structural changes or retention, sources consulted/reused, preservation checks and substantive unresolved issues. Keep working notes concise and provide them only when useful or requested.

[profile.json](profile.json) separates corpus and annotation denominators. [structure-evidence.md](references/structure-evidence.md) and [local-evidence.md](references/local-evidence.md) document historical observations; the new editorial operations and synthetic examples are design candidates, not measured human benefits. Never output an AI-authorship probability or a single human-likeness score.

The optional [outline helper](scripts/check_outline.py), documented in [outline-contract.md](references/outline-contract.md), checks IDs, coverage and references only. A `pass` does not show that evidence entails a claim, that the physics is correct or that readers understand it. No formal JSON ledger is needed for normal writing.
