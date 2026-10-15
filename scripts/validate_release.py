import sys,subprocess,re,resource,time,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.common import *
result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],capture_output=True,text=True);Path('reports/test_run.txt').write_text(result.stdout+result.stderr);count=re.search(r'Ran (\d+) tests',result.stderr)
if result.returncode:raise SystemExit(result.stdout+result.stderr)
skill=subprocess.run([sys.executable,str(Path.home()/'.codex/skills/.system/skill-creator/scripts/quick_validate.py'),'skills/physics-paper-style'],env=__import__('os').environ|{'PYTHONPATH':'.devdeps'},capture_output=True,text=True)
if skill.returncode:raise SystemExit(skill.stdout+skill.stderr)
from physstyle.pipeline import run
request_hash=digest(Path('data/raw/http/requests.jsonl').read_bytes());label_hash=digest(Path('data/annotations/labels.jsonl').read_bytes());started=time.monotonic();run(read_json('configs/smoke.json'),offline=True);elapsed=time.monotonic()-started
profiles=digest(Path('data/features/feature_profiles.json').read_bytes())
# Recompute statistics without source acquisition, parsing or model work to test determinism.
from physstyle.pipeline import analyze
analyze(read_json('configs/smoke.json'))
assert profiles==digest(Path('data/features/feature_profiles.json').read_bytes()),'statistics nondeterministic'
assert request_hash==digest(Path('data/raw/http/requests.jsonl').read_bytes()),'offline replay made requests'
assert label_hash==digest(Path('data/annotations/labels.jsonl').read_bytes()),'offline replay changed labels'
from physstyle.annotations import validate_record
ws={w['window_id']:w for w in read_jsonl('data/annotations/tasks.jsonl')};records=read_jsonl('data/annotations/labels.jsonl')
for record in records:validate_record(record,ws)
code_hash=hashlib.sha256()
for directory in ['physstyle','scripts','tests']:
 for p in sorted(Path(directory).rglob('*.py')):code_hash.update(str(p).encode()+b'\0'+p.read_bytes())
validation={'validated_at':now(),'tests_command':'python3 -m unittest discover -s tests -v','tests_passed':True,'test_count':int(count[1]),'skill_validator_passed':True,'skill_validator_output':skill.stdout.strip(),'validated_annotation_records':len(records),'offline_no_new_http_requests':True,'offline_labels_unchanged':True,'fixed_annotations_statistics_reproducible':True,'source_reparse_elapsed_seconds':round(elapsed,3),'max_resident_set_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'code_tree_sha256':code_hash.hexdigest(),'git_status':'not_a_git_repository; no commit/push performed','independent_review':'reports/semantic_audit.json; code and semantic review; experiments separately independently agent-reviewed','human_review':False}
write_json('reports/validation.json',validation)
from physstyle.report import finalize_results
finalize_results();print(json.dumps(validation,ensure_ascii=False,indent=2))
