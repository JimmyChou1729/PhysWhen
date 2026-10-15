# PhysWhen

> AI can code. AI can do math. Physics when?

**An agent skill for clearer theoretical-physics papers—from whole-paper structure to sentence-level editing.**

English | [简体中文](README.zh-CN.md)

Physics papers can be hard to follow even when every sentence is grammatical. Late assumptions, derivations disconnected from the research question, and conclusions that exceed the evidence all reduce readability. PhysWhen turns source-traceable observations from historical research papers into practical writing instructions for an agent.

## Quick start

Clone the repository, or download the [portable skill ZIP](deliverables/PhysWhen-skill.zip).

```bash
git clone https://github.com/jimmychou1729/PhysWhen.git
cd PhysWhen
```

For Codex, copy the **whole** `skills/physwhen/` folder into your personal skill directory. This first-install command leaves an existing installation untouched:

```bash
mkdir -p "$HOME/.agents/skills"
if [ ! -e "$HOME/.agents/skills/physwhen" ]; then
  cp -R skills/physwhen "$HOME/.agents/skills/"
else
  echo "physwhen is already installed; see docs/USAGE.md to update it."
fi
```

Select `physwhen` in your skill picker; Codex CLI and IDE also support `$physwhen`. If it does not appear, restart the client. See the [official skill documentation](https://learn.chatgpt.com/docs/build-skills) for discovery paths. Other compatible agents should receive the complete folder through their own installation mechanism; they have not all been tested here.

### ChatGPT web and Dot

Use the [plugin ZIP](deliverables/PhysWhen-plugin.zip) through a supported account-plugin import flow; the standalone skill ZIP is not a plugin. Both packages contain the same maintained skill. The plugin adds a portable manifest and needs no MCP server. Availability depends on the host and account; packaging alone does not establish a successful ChatGPT or Dot run. See [host setup and verification (Chinese)](docs/HOSTS.md).

## Usage

Example requests:

> Use physwhen to revise this paper.

> Use physwhen to write a cosmology paper from these research notes.

> Use physwhen to improve this paragraph.

> Use physwhen to review draft.tex. Propose a new outline without editing the file. The audience knows cosmology but not this model.

> Use physwhen to turn notes.md into a 2,500-word English draft. Keep the supplied results and flag missing material separately.

> Use physwhen to polish only these two paragraphs, preserving the notation and assumptions.

These extra instructions are optional. Full-paper organization, local editing, and the optional outline checker are explained in the [usage guide (Chinese)](docs/USAGE.md).

## What it does

| Task | What PhysWhen considers |
| --- | --- |
| Plan a paper | The question, supplied results, prerequisites, and possible argument routes |
| Revise a draft | Dependencies, branching cases, previews, development, and useful recaps |
| Allocate detail | Which logical bridges belong in the main text and which details can be deferred |
| Edit paragraphs | The purpose of equations, interpretation of results, and conditions attached to claims |

Scientific content remains authoritative. PhysWhen does not invent evidence, citations, novelty, or missing proofs. It is not an AI detector or a substitute for scientific review.

## How it works

Historical papers → parsing with source locations → automatic features and semantic annotation → independent review → candidate writing operations → writing comparisons and reader studies.

The skill uses four organizational operations and three local prose operations, each with conditions and exceptions. Historical frequency supplies descriptive evidence, not proof of an ideal writing style. See the [research method (Chinese)](docs/RESEARCH.md) and the skill's [source-backed references](skills/physwhen/references/structure-evidence.md).

| Evidence | Current scope |
| --- | --- |
| Historical corpus | 500 papers from 2010–2021; 400 discovery / 100 heldout |
| Fields | gr-qc: 200; astro-ph.CO: 150; hep-th: 150 |
| Whole-paper structure annotation | 30 complete main bodies with selective argument graphs—not 500 fully annotated papers |
| Local annotation | 27 papers / 120 windows, reported separately from structure annotation |
| Human readability benefit | **Not established; reader evaluation is ongoing** |

The [cosmology blind test](deliverables/PhysWhen-Blind-Test-03.html) presents three pairs of paper-style texts and collects one overall preference per pair. Download the HTML and open it in a desktop browser. Responses are exported as JSON and returned to the organizer; there is no automatic upload. It is a frozen study, not automatically regenerated whenever the skill changes.

## Development

Using the skill does not require Python. The optional checker and research tools require Python 3.10+ and use the standard library.

```bash
python3 skills/physwhen/scripts/check_outline.py examples/outline.json
python3 -m unittest discover -s tests -p 'test_outline.py' -v
python3 scripts/package_skill.py --check
```

The example is synthetic interface data. A successful check verifies structural references, not scientific validity or readability. See [development and reproduction (Chinese)](docs/DEVELOPMENT.md) for the portable test suite and the local-data requirements of historical research scripts.

```text
skills/physwhen/   The single maintained skill and its references
examples/         Synthetic interface examples
physstyle/        Research and feedback tools
scripts/          Packaging, analysis, and validation
reader/           Anonymous reading-study frontend
deliverables/     Portable skill and reader files
docs/             Usage, research, development, and publishing notes
```

## Data and licensing

Paper full texts, raw caches, complete annotation contexts, condition mappings, and participant responses stay outside Git. The skill includes descriptive statistics and source locators rather than paper full texts.

PhysWhen's original code, skill instructions, documentation, and generated study materials are licensed under the [MIT License](LICENSE). You may use, modify, redistribute, and use them commercially, provided you retain the copyright and license notice. The software is provided without warranty.

This license does not relicense the historical papers or third-party components. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for their terms and [PUBLISHING.md (Chinese)](docs/PUBLISHING.md) for publication boundaries.
