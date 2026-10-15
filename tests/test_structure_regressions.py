"""500-stage regression tests using isolated files, locks and mocked acquisition."""
import contextlib
import copy
import io
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

from physstyle.common import digest, read_json, read_jsonl, write_json, write_jsonl
from physstyle.pipeline import run
from physstyle.pilot import analyze_pilot
from physstyle.structure_corpus import analyze


REPO = Path(__file__).resolve().parents[1]
COLLECTOR = REPO / "scripts" / "collect_structure500.py"


class StructureRegressionTests(unittest.TestCase):
    def setUp(self):
        previous = Path.cwd()
        temporary = tempfile.TemporaryDirectory(prefix="physwhen-structure-regression-")
        self.addCleanup(temporary.cleanup)
        self.addCleanup(os.chdir, previous)
        os.chdir(temporary.name)

    def run_collector(self):
        # run_path inserts the repository into sys.path; contain that side effect too.
        with patch.object(sys, "path", list(sys.path)), contextlib.redirect_stdout(io.StringIO()):
            return runpy.run_path(str(COLLECTOR), run_name="__main__")

    def test_snapshot_routes_exactly_210_papers_without_touching_old_results(self):
        rows = [
            {"paper_id": str(i), "screening": "include", "parse_status": "usable"}
            for i in range(210)
        ]
        write_jsonl("data/manifests/corpus.jsonl", rows)
        write_jsonl("reports/cohort210_snapshot/corpus.jsonl", rows)
        sentinels = {
            "reports/PILOT_RESULTS.json": {"frozen": "pilot result"},
            "data/features/pilot/feature_profiles.json": {"frozen": "pilot profile"},
        }
        for path, value in sentinels.items():
            write_json(path, value)
        cfg = {"interval": 0, "retries": 0, "max_download_bytes": 100, "max_raw_bytes": 100}
        with patch("physstyle.structure_corpus.analyze", return_value={"structure": "fixture"}) as routed, patch(
            "physstyle.pipeline.Fetcher", side_effect=AssertionError("legacy route reached")
        ) as fetcher:
            self.assertEqual(run(cfg, offline=True), {"structure": "fixture"})
            self.assertEqual(analyze_pilot(), {"structure": "fixture"})
            self.assertEqual(routed.call_count, 2)
            fetcher.assert_not_called()
        for path, value in sentinels.items():
            self.assertEqual(read_json(path), value)

    def test_snapshot_rejects_old_online_acquisition_entrypoint(self):
        write_jsonl("reports/cohort210_snapshot/corpus.jsonl", [])
        with patch("physstyle.pipeline.Fetcher", side_effect=AssertionError("network initialized")) as fetcher:
            with self.assertRaisesRegex(ValueError, "collect_structure500"):
                run({}, offline=False)
            fetcher.assert_not_called()

    def test_collector_resume_assigns_new_metadata_and_preserves_old_batches(self):
        cfg = {
            "interval": 0, "retries": 0, "max_download_bytes": 10000,
            "max_raw_bytes": 10000, "years": [2020], "categories": ["gr-qc"],
            "extension_per_stratum": 1, "candidate_cap": 10, "target": 500,
        }
        write_json("configs/structure500.json", cfg)
        write_json("data/manifests/sampling.json", {
            "2020:gr-qc": {"total": 10, "random_block_start": 0, "returned": 1}
        })
        write_json("data/manifests/structure_sampling.json", {
            "2020:gr-qc": {"status": "failed", "error": "previous temporary error"}
        })
        old = {
            "paper_id": "2001.00001", "title": "Old", "abstract": "Old abstract",
            "categories": ["gr-qc"], "sampling_stratum": "2020:gr-qc",
            "sampling_year": 2020, "sampling_category": "gr-qc", "stratum_rank": 16,
            "sampling_cohort": "structure500_extension", "screening": "unresolved",
            "task_snapshot_marker": "keep the old row exactly",
        }
        new = {
            "paper_id": "2001.00002", "title": "New", "abstract": "New abstract",
            "categories": ["gr-qc"],
        }
        write_jsonl("data/manifests/candidates.jsonl", [old])
        for suffix, batch in [("a", [old]), ("b", []), ("c", [])]:
            write_jsonl(f"data/manifests/structure_scope_batch_{suffix}.jsonl", batch)
        write_jsonl("data/manifests/structure_scope_decisions_a.jsonl", [{
            "paper_id": old["paper_id"], "screening": "exclude", "screening_reason": "fixture",
            "screening_source_sha256": digest((old["title"] + "\n" + old["abstract"]).encode()),
        }])
        with patch("physstyle.network.Fetcher") as fetcher, patch(
            "physstyle.corpus.atom", return_value=(10, [copy.deepcopy(new)])
        ), patch("physstyle.corpus.acquire", side_effect=AssertionError("unreviewed source acquired")) as acquire, patch(
            "time.time", side_effect=[0, 14401]
        ), patch("time.sleep", side_effect=AssertionError("test must not wait")):
            fetcher.return_value.get.return_value = (b"mock metadata", {})
            self.run_collector()
            fetcher.return_value.get.assert_called_once()
            acquire.assert_not_called()
        batches = {
            suffix: read_jsonl(f"data/manifests/structure_scope_batch_{suffix}.jsonl")
            for suffix in ("a", "b", "c")
        }
        self.assertEqual(batches["a"], [old])
        assigned = [r["paper_id"] for batch in batches.values() for r in batch]
        self.assertCountEqual(assigned, [old["paper_id"], new["paper_id"]])
        self.assertEqual(len(assigned), len(set(assigned)))
        self.assertEqual(read_json("data/manifests/structure_sampling.json")["2020:gr-qc"]["status"], "complete")

    def test_completed_collector_exits_before_initializing_network(self):
        # No sampling configuration exists: completed runs must not even reach it.
        write_json("configs/structure500.json", {"target": 1})
        write_jsonl("data/manifests/corpus.jsonl", [{"screening": "include", "parse_status": "usable"}])
        with patch("physstyle.network.Fetcher", side_effect=AssertionError("network initialized")) as fetcher:
            with self.assertRaises(SystemExit) as exit_context:
                self.run_collector()
            self.assertEqual(exit_context.exception.code, 0)
            fetcher.assert_not_called()

    def test_sampling_failure_report_tracks_failure_then_recovery(self):
        write_jsonl("data/manifests/corpus.jsonl", [])
        write_json("reports/cohort210_snapshot/frozen.json", {"assignments": {}})
        complete = {"status": "complete", "returned": 1}
        failure = {"status": "failed", "error": "fixture HTTP503", "start": 4}
        write_json("data/manifests/structure_sampling.json", {
            "2020:gr-qc": complete, "2021:gr-qc": failure,
        })
        with contextlib.redirect_stdout(io.StringIO()):
            failed_result = analyze()
        self.assertEqual(failed_result["sampling_extension_status_counts"], {"complete": 1, "failed": 1})
        self.assertEqual(failed_result["sampling_extension_failures"], {"2021:gr-qc": failure})
        write_json("data/manifests/structure_sampling.json", {
            "2020:gr-qc": complete, "2021:gr-qc": complete,
        })
        with contextlib.redirect_stdout(io.StringIO()):
            recovered_result = analyze()
        self.assertEqual(recovered_result["sampling_extension_status_counts"], {"complete": 2})
        self.assertEqual(recovered_result["sampling_extension_failures"], {})
        self.assertNotIn("three extension strata failed HTTP429", recovered_result["sampling_limits"])
        self.assertEqual(read_json("reports/STRUCTURE_RESULTS.json"), recovered_result)


    def test_unknown_adjudication_operation_is_rejected_before_replay(self):
        protocol = read_json(REPO / "data/structure/protocol.json")
        packet = {
            "paper_id": "fixture", "version": 1, "source_sha256": "fixture hash", "split": "discovery",
            "main_body_paragraph_ids": ["p1"],
            "paragraphs": [{"paragraph_id": "p1", "word_count": 1, "blocks": [{"raw": "Result."}]}],
        }
        record = {
            "protocol_version": protocol["version"], "paper_id": "fixture", "version": 1,
            "source_sha256": "fixture hash", "split": "discovery",
            "coverage": {"main_body": "full_read", "abstract": "read", "figures": "not_read", "appendices": "not_read"},
            "moves": [{"start_paragraph_id": "p1", "end_paragraph_id": "p1", "role": "result",
                       "evidence": [{"paragraph_id": "p1", "exact_quote": "Result."}], "rationale": "fixture"}],
            "nodes": [], "edges": [], "question_status": [], "recurrences": [], "quality_notes": [],
        }
        write_json("data/structure/protocol.json", protocol)
        write_json("data/structure/papers/fixture.json", packet)
        initial = Path("data/structure/initial_annotations/fixture.json")
        write_json(initial, record)
        initial_bytes = initial.read_bytes()
        write_json("data/structure/initial_annotation_hashes.json", {
            "files": [{"path": str(initial), "sha256": digest(initial_bytes)}]
        })
        write_json("data/structure/annotations/fixture.json", record)
        write_jsonl("data/structure/adjudications.jsonl", [{
            "decision": "accept", "paper_id": "fixture", "operation": "replcae",
            "path": "/quality_notes", "original": [], "suggested": ["approved correction"],
        }])
        with patch.object(sys, "path", list(sys.path)), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "unknown adjudication operation"):
                runpy.run_path(str(REPO / "scripts/apply_structure_adjudications.py"), run_name="__main__")
        self.assertEqual(read_json("data/structure/annotations/fixture.json"), record)
        self.assertEqual(initial.read_bytes(), initial_bytes)

    def test_supplement_rejects_stale_complete_report_before_freezing_tasks(self):
        write_json("reports/STRUCTURE_RESULTS.json", {"papers_usable": 500})
        rows, assignments = [], {}
        source = b"synthetic source"
        for category_index, category in enumerate(("gr-qc", "astro-ph.CO", "hep-th")):
            for year in (2011, 2017):
                pid = f"fixture{category_index}_{year}"
                rows.append({
                    "paper_id": pid, "screening": "include", "parse_status": "usable",
                    "sampling_category": category, "sampling_year": year, "title": "Fixture",
                    "abstract": "Fixture", "version": 1, "source_sha256": digest(source),
                })
                assignments[pid] = "discovery"
                raw = Path(f"data/raw/papers/{pid}v1/source.bin")
                raw.parent.mkdir(parents=True, exist_ok=True)
                raw.write_bytes(source)
                write_json(f"data/parsed/{pid}.json", {
                    "paper_id": pid, "version": 1, "source_sha256": digest(source),
                    "split": "discovery", "main_prose_words": 900,
                    "source_root": str(raw.parent / "source"), "source_files": {},
                    "sections": [], "warnings": [], "paragraphs": [{
                        "paragraph_id": "p1", "section_role": "technical_body", "word_count": 900,
                        "blocks": [{"raw": "Result. " * 900}],
                    }],
                })
        write_jsonl("data/manifests/corpus.jsonl", rows)
        write_jsonl("reports/cohort210_snapshot/corpus.jsonl", [])
        write_json("data/splits/frozen.json", {"assignments": assignments})
        with patch.object(sys, "path", list(sys.path)), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "current corpus does not match"):
                runpy.run_path(str(REPO / "scripts/prepare_structure_supplement.py"), run_name="__main__")
        self.assertFalse(Path("data/structure/supplement_sample.json").exists())
        self.assertFalse(Path("data/structure/papers").exists())
        self.assertFalse(list(Path("data/structure").glob("supplement_assignment_*.json")))



    def test_inactive_historical_assignment_is_preserved_but_not_counted(self):
        old_assignments = {"old_active": "discovery", "old_excluded": "heldout"}
        write_json("reports/cohort210_snapshot/frozen.json", {"assignments": old_assignments})
        write_json("data/splits/frozen.json", {
            "seed": 1729, "assignments": old_assignments, "family_matches": [], "next_family_index": 2,
        })
        write_json("configs/features.json", {"D06": {}})
        legacy_result = {"frozen": "historical result"}
        write_json("reports/PILOT_RESULTS.json", legacy_result)
        rows = []
        for pid, title, category in [
            ("old_active", "Gravity near a horizon", "gr-qc"),
            ("new_active", "Supersymmetric gauge spectra", "hep-th"),
        ]:
            source = (title + " source bytes").encode()
            source_path = Path(f"data/raw/papers/{pid}v1/source.bin")
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_bytes(source)
            row = {
                "paper_id": pid, "title": title, "authors": [pid + " author"],
                "screening": "include", "parse_status": "usable", "version": 1,
                "source_sha256": digest(source), "version_identity_verified": True,
                "sampling_category": category, "sampling_year": 2015,
            }
            rows.append(row)
            write_json(f"data/parsed/{pid}.json", {
                "paper_id": pid, "version": 1, "source_sha256": digest(source), "usable": True,
                "normalized_body_sha256": digest((title + " normalized body").encode()),
                "source_root": str(source_path.parent / "source"), "main_prose_words": 3,
                "paragraphs": [{
                    "paragraph_id": "p1", "section_id": "s1", "section_title": "Introduction",
                    "section_role": "introduction", "word_count": 3, "blocks": [{
                        "block_id": "b1", "kind": "prose", "raw": "Active fixture text.",
                        "text": "Active fixture text.", "refs": [],
                        "source_spans": [{"source_file": "main.tex", "line_start": 1, "line_end": 1}],
                    }],
                }],
            })
        # Deliberately no parsed file/source for the excluded historical paper:
        # preservation of its ledger entry must not turn it into an active input.
        rows.append({
            "paper_id": "old_excluded", "screening": "exclude", "parse_status": "usable", "version": 1,
        })
        write_jsonl("data/manifests/corpus.jsonl", rows)
        with contextlib.redirect_stdout(io.StringIO()):
            result = analyze()
        assignments = read_json("data/splits/frozen.json")["assignments"]
        self.assertEqual({pid: assignments[pid] for pid in old_assignments}, old_assignments)
        self.assertEqual(set(assignments), {"old_active", "old_excluded", "new_active"})
        self.assertEqual(result["papers_usable"], 2)
        self.assertEqual(result["automatic_navigation_papers"], 2)
        self.assertEqual(result["source_versions_verified"], 2)
        self.assertEqual(result["split_counts"], {"discovery": 2})
        self.assertEqual(result["scope_excluded_after_acquisition"], 1)
        self.assertEqual(
            {r["paper_id"] for r in read_jsonl("data/features/structure500/evidence_index.jsonl")},
            {"old_active", "new_active"},
        )
        profiles = read_json("data/features/structure500/feature_profiles.json")
        self.assertEqual(profiles["discovery"]["D01_sentence_median"]["n"], 2)
        self.assertEqual(profiles["heldout_frozen_check"], {})
        self.assertFalse(Path("data/features/structure500/papers/old_excluded.json").exists())
        self.assertEqual(read_json("reports/PILOT_RESULTS.json"), legacy_result)
        # The change must not weaken preservation: even an inactive assignment
        # being altered is still an error, rather than merely being ignored.
        ledger = read_json("data/splits/frozen.json")
        ledger["assignments"]["old_excluded"] = "discovery"
        write_json("data/splits/frozen.json", ledger)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "existing cohort split changed"):
                analyze()



if __name__ == "__main__":
    unittest.main()
