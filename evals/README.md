# Diagnostic evaluation

This suite tests editorial operations on **synthetic material**, not real-paper discoveries or human readability. The maintained skill remains `physwhen`; these files describe one frozen evaluation cycle.

The completed pilot is documented in [results](diagnostic/RESULTS.md), with [all initial/final manuscripts](diagnostic/run.json) and [anonymous model judgments](diagnostic/model-screen.json). Candidate finals were judged clear and preserved in 12/12 cases, versus 11/12 in each other condition; the difference arose in one case and does not establish a stable or human benefit. These are short synthetic paragraphs, not full-paper cosmology validation.

`diagnostic/development.jsonl` contains 12 development cases. Another 12 cases were authored independently without access to the candidate instructions, kept outside the candidate author's view until the candidate resource hashes were frozen, then exported to three isolated writing conditions. The cases cover coherence, terminology, scientific fidelity and organization; each split has six drafting and six editing tasks. Correct or deliberately specialized inputs test when an edit should stop.

The sealed set is published after this run for transparency. It is **retired as an unseen test** for future rule tuning. Replays on it are regression checks, not fresh holdout evidence. This synthetic split is separate from the historical corpus's frozen 400/100 split.

## Controlled comparison

- Strong generic scientific-writing instructions.
- Frozen PhysWhen from commit `a059a92e196679d6f0dc54dc8d02ba2ff18155ed`.
- Candidate frozen before opening the sealed cases.

Each condition receives identical scientific material, audience, word limit and source access. External retrieval is explicitly disabled for this benchmark, with the limitation disclosed; it remains the normal product requirement. This isolates the editorial package from retrieval quality. It does not isolate the historical corpus contribution from every other prompt difference.

Fresh independent agent contexts generate one initial draft and one checked final per case. Initial files are retained before checking. Exact model ID, temperature and sampling seed are unavailable; no paid API or fine-tuning is used. No regeneration is selected on preference. Sources and task identities are hash-bound to outputs; the writing jobs omit scoring hints and expected comprehension points.

Anonymous final manuscripts are screened independently against per-case facts and editorial criteria. Alias order is randomly generated; the private mapping is withheld from the reviewer. This is label masking with instructions restricting access, not a cryptographic access-control boundary or a verified human blind study. Reports separate drafting from editing. Literal and length flags are review hints only, not semantic judgments. Fidelity-changed/uncertain texts do not count as readability successes.

First drafts are retained, but the initial model screen evaluates final manuscripts. This run therefore does not establish an isolated first-pass-generation benefit. Human comprehension and end-to-end live retrieval remain separate follow-up work.

## Reproduce exports and imports

The script never calls a model. From a checkout containing the baseline Git history:

```bash
python3 scripts/writing_eval.py validate-cases evals/diagnostic/development.jsonl
python3 -m unittest discover -s tests -p 'test_writing_eval.py' -v
```

To start a new cycle, place an immutable baseline skill copy and a candidate copy in separate local directories, then freeze the candidate before opening new test cases:

```bash
python3 scripts/writing_eval.py freeze skills/physwhen reports/new-cycle/candidate-freeze.json
python3 scripts/writing_eval.py export --cases evals/diagnostic/check.jsonl --rubric evals/diagnostic/check-rubric.jsonl --protocol evals/diagnostic/protocol.json --baseline reports/diagnostic_cycle/baseline --candidate skills/physwhen --freeze reports/new-cycle/candidate-freeze.json --output reports/new-cycle/jobs
```

The baseline copy in the example must first be restored from the recorded commit; it is not present in a fresh checkout. Preserve files by commit and relative path, e.g. use `git archive` to a temporary directory. Current `check.jsonl` is published regression material, not a new unseen test.

The exporter binds the supplied baseline directory's hashes; it does not automatically prove those bytes came from `baseline_commit`. Compare that directory with the recorded Git commit and [baseline manifest](diagnostic/baseline.json) before exporting. That comparison was completed for this run.

Use fresh model contexts to execute each arm's exported job directory. Each response JSON must contain `case_id`, exact `job_id`, `first_draft`, `manuscript`, `note`, and `checks_performed`. Record actual resource reads and hashes. Store real initial drafts before final checks; do not populate outputs with mock data or reference rewrites.

```bash
python3 scripts/writing_eval.py collect --cases evals/diagnostic/check.jsonl --jobs reports/new-cycle/jobs --responses reports/new-cycle/responses --output reports/new-cycle/collected.json
python3 scripts/writing_eval.py prepare-review --cases evals/diagnostic/check.jsonl --rubric evals/diagnostic/check-rubric.jsonl --collected reports/new-cycle/collected.json --output reports/new-cycle/review
```

Give only the `review/masked` directory to a separate reviewer. Judgments use `case_id`, `review_packet_id`, `alias`, `fidelity` (`preserved/changed/uncertain`), `clarity` (`clear/mixed/problematic/unrated`), `defect_resolution` (`resolved/partial/unresolved/not_applicable`), `unnecessary_rewrite` (`yes/no/uncertain`), `fact_checks` and `notes`. Fact checks follow the provided required-facts order and contain `fact`, `status`, `evidence_quote` and `reason`. A preservation judgment needs an exact quote from the final manuscript; a quote alone still does not establish semantic correctness.

```bash
python3 scripts/writing_eval.py summarize-review --review-root reports/new-cycle/review --judgments reports/new-cycle/judgments.jsonl --output reports/new-cycle/model-screen.json
python3 scripts/writing_eval.py export-human --review-root reports/new-cycle/review --output reports/new-cycle/optional-human-forms
```

Human exports contain one anonymous version per case and two short comprehension questions; three form variants rotate assignments. Expected answer points are omitted. These are optional study materials, not collected participant data. Leave the existing preference-only group HTML unchanged. No results are uploaded automatically; raw reader responses must remain outside Git.
