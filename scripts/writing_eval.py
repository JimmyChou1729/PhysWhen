"""Reproducible case export/import and masked review for synthetic writing evaluation.

Uses only standard library; never calls a model or treats automated flags as semantic scores.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess

FAMILIES = {'coherence', 'terminology', 'fidelity', 'organization'}
ARMS = ('generic', 'baseline', 'candidate')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def validate_cases(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('cases must be a nonempty list')
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('id'),str) or not re.fullmatch('[DH][0-9]{2}', row.get('id', '')) or row['id'] in ids:
            raise ValueError('invalid/duplicate case id')
        ids.add(row['id'])
        if row.get('family') not in FAMILIES or row.get('mode') not in ('draft', 'edit'):
            raise ValueError('invalid family or mode')
        for field in ('task_type', 'audience', 'instruction', 'material', 'source_status'):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError('missing case field: ' + field)
        if 'synthetic' not in row['source_status']:
            raise ValueError('synthetic provenance required')
        for field in ('required_literals', 'forbidden_literals'):
            if not isinstance(row.get(field), list) or not all(isinstance(x, str) and x for x in row[field]):
                raise ValueError('invalid literal hints')
        if type(row.get('word_limit')) is not int or not 30 <= row['word_limit'] <= 2000:
            raise ValueError('invalid word limit')
    return rows

def source_files(root):
    root = Path(root)
    out = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('skill symlink is not allowed')
        if path.is_file() and '__pycache__' not in path.parts:
            out[str(path.relative_to(root))] = digest(path.read_bytes())
    if 'SKILL.md' not in out:
        raise ValueError('skill source missing')
    return out

def freeze_candidate(root, dest):
    """Write once before sealed cases are opened; reject accidental refreezing."""
    dest = Path(dest)
    if dest.exists():
        raise ValueError('candidate freeze already exists; use a new evaluation cycle')
    files = source_files(root)
    write_json(dest, {'schema': 'physwhen.candidate.freeze.v1', 'files': files,
                      'bundle_sha256': digest(json.dumps(files, sort_keys=True).encode())})
    return files

def verify_candidate(root, freeze):
    if source_files(root) != json.loads(Path(freeze).read_text())['files']:
        raise ValueError('candidate changed after freeze')

def export_jobs(cases_path, protocol_path, baseline_root, candidate_root, candidate_freeze, output, rubric_path):
    rows = validate_cases(read_lines(cases_path)); output = Path(output)
    if output.exists():
        raise ValueError('job directory exists; do not overwrite previous generations')
    verify_candidate(candidate_root, candidate_freeze)
    protocol = json.loads(Path(protocol_path).read_text())
    sources = {'baseline': {'path': str(Path(baseline_root).resolve()), 'files': source_files(baseline_root)},
               'candidate': {'path': str(Path(candidate_root).resolve()), 'files': source_files(candidate_root)}}
    output.mkdir(parents=True)
    job_hashes={};common_hashes={}
    for arm in ARMS:
        common = {'arm': arm, 'cases_sha256': digest(Path(cases_path).read_bytes()),
                  'protocol_sha256': digest(Path(protocol_path).read_bytes()),
                  'source': sources.get(arm), 'generic_prompt': protocol['generic_prompt'] if arm == 'generic' else None,
                  'generation_contract': protocol['generation'], 'model_id': None, 'temperature': None, 'seed': None,
                  'output_schema': {'job_id':'copy the per-case job_id exactly', 'case_id': 'matching id', 'first_draft': 'initial manuscript', 'manuscript': 'checked final manuscript', 'note': 'separate note', 'checks_performed': 'short list of actual checks'}}
        common_path=output / arm / 'job.json';write_json(common_path, common);common_hashes[arm]=digest(common_path.read_bytes());job_hashes[arm]={}
        for row in rows:
            # Expected facts/answers and literal check hints never enter generation jobs.
            public = {k: row[k] for k in ('id','family','mode','task_type','audience','instruction','material','word_limit','source_status')}
            public['job_id']=digest(json.dumps({'arm':arm,'case':public,'cases_sha256':common['cases_sha256'],'protocol_sha256':common['protocol_sha256'],'source':common['source']},sort_keys=True).encode())
            dest=output / arm / (row['id']+'.json');write_json(dest,public);job_hashes[arm][row['id']]=digest(dest.read_bytes())
    write_json(output / 'manifest.json', {'schema': 'physwhen.writing.jobs.v1', 'case_ids': [r['id'] for r in rows],
                                        'cases_sha256': digest(Path(cases_path).read_bytes()), 'sources': sources,
                                        'candidate_freeze_sha256': digest(Path(candidate_freeze).read_bytes()),
                                        'protocol_path':str(Path(protocol_path).resolve()),'protocol_sha256':digest(Path(protocol_path).read_bytes()),'rubric_path':str(Path(rubric_path).resolve()),'rubric_sha256':digest(Path(rubric_path).read_bytes()),'job_hashes':job_hashes,'common_hashes':common_hashes,'arms': list(ARMS), 'human_effect': 'not_established'})
    return len(rows) * len(ARMS)

def validate_output(obj, expected_id, expected_job):
    if not isinstance(obj, dict) or obj.get('case_id') != expected_id:
        raise ValueError('output identity mismatch')
    if obj.get('job_id')!=expected_job:raise ValueError('output job/protocol/source identity mismatch')
    for key in ('first_draft','manuscript','note'):
        if not isinstance(obj.get(key), str) or len(obj[key]) > 30000 or (key != 'note' and not obj[key].strip()):
            raise ValueError('invalid output field: ' + key)
    if not isinstance(obj.get('checks_performed'), list) or not all(isinstance(x,str) for x in obj['checks_performed']):
        raise ValueError('invalid checks_performed')
    return obj

def normalized(text):
    return re.sub(r'\s+', '', text).replace('$','').replace('\\(','').replace('\\)','')

def collect(cases_path, jobs_root, responses_root, output):
    cases = validate_cases(read_lines(cases_path)); jobs = json.loads((Path(jobs_root)/'manifest.json').read_text())
    if jobs['cases_sha256'] != digest(Path(cases_path).read_bytes()) or set(jobs['case_ids']) != {r['id'] for r in cases}:
        raise ValueError('cases changed after export')
    for path_key,sha_key in [('protocol_path','protocol_sha256'),('rubric_path','rubric_sha256')]:
        if digest(Path(jobs[path_key]).read_bytes())!=jobs[sha_key]:raise ValueError('protocol/rubric changed after export')
    for arm,source in jobs['sources'].items():
        if source_files(source['path'])!=source['files']:raise ValueError('source changed after export: '+arm)
    records = []; missing = []
    for case in cases:
        for arm in jobs['arms']:
            jobpath=Path(jobs_root)/arm/(case['id']+'.json')
            if digest(jobpath.read_bytes())!=jobs['job_hashes'][arm][case['id']]:raise ValueError('job changed after export')
            commonpath=Path(jobs_root)/arm/'job.json'
            if digest(commonpath.read_bytes())!=jobs['common_hashes'][arm]:raise ValueError('arm contract changed after export')
            path = Path(responses_root)/arm/(case['id']+'.json')
            if not path.is_file():
                missing.append(arm+':'+case['id']); continue
            record = validate_output(json.loads(path.read_text()), case['id'],json.loads(jobpath.read_text())['job_id'])
            flags = []
            for phase in ('first_draft','manuscript'):
                text = normalized(record[phase])
                for item in case['required_literals']:
                    if normalized(item) not in text: flags.append({'phase':phase,'kind':'literal_not_found','text':item})
                for item in case['forbidden_literals']:
                    if normalized(item) in text: flags.append({'phase':phase,'kind':'forbidden_literal_found','text':item})
                n = len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*", record[phase]))
                if n > case['word_limit']: flags.append({'phase':phase,'kind':'length_review','words':n,'limit':case['word_limit']})
            records.append({'case_id':case['id'],'arm':arm,'source_sha256':digest(path.read_bytes()),
                            'output':record,'flags':flags})
    write_json(output, {'schema':'physwhen.writing.collected.v1','records':records,'missing':missing,'cases_sha256':jobs['cases_sha256'],'rubric_sha256':jobs['rubric_sha256'],'job_manifest_sha256':digest((Path(jobs_root)/'manifest.json').read_bytes()),
                        'flag_limits':'Literal hints and word counts only; no semantic fidelity or quality judgment.',
                        'human_effect':'not_established'})
    return len(records), len(missing)

def prepare_review(cases_path, rubric_path, collected_path, output, seed=None):
    cases = {r['id']:r for r in validate_cases(read_lines(cases_path))}
    rubric_rows=read_lines(rubric_path)
    if any(not isinstance(r,dict) or not isinstance(r.get('case_id'),str) for r in rubric_rows):raise ValueError('invalid rubric row')
    rubrics = {r['case_id']:r for r in rubric_rows}
    if len(rubrics)!=len(rubric_rows):raise ValueError('duplicate rubric identity')
    if set(cases) != set(rubrics): raise ValueError('rubric/case mismatch')
    collected = json.loads(Path(collected_path).read_text())
    if collected.get('cases_sha256')!=digest(Path(cases_path).read_bytes()) or collected.get('rubric_sha256')!=digest(Path(rubric_path).read_bytes()):raise ValueError('review cases/rubric differ from collected generation')
    if collected['missing']: raise ValueError('cannot review incomplete comparison')
    output = Path(output)
    if output.exists(): raise ValueError('review directory already exists')
    rng = random.SystemRandom() if seed is None else random.Random(seed); by_case = {}
    for rec in collected['records']:
        group=by_case.setdefault(rec['case_id'], {})
        if rec['arm'] in group: raise ValueError('duplicate case/arm record')
        group[rec['arm']] = rec['output']
    if set(by_case)!=set(cases): raise ValueError('collected/case mismatch')
    key = {}; packet_hashes={}
    for cid in sorted(cases):
        if set(by_case[cid]) != set(ARMS): raise ValueError('arm coverage mismatch')
        arms = list(ARMS);rng.shuffle(arms); key[cid] = dict(zip(['U','V','W'], arms))
        # Reference case/rubric plus anonymous manuscripts. Never arm prompts or writer notes.
        packet={'case':cases[cid], 'rubric':rubrics[cid],
                'texts':{alias:{'first_draft':by_case[cid][arm]['first_draft'],'manuscript':by_case[cid][arm]['manuscript']} for alias,arm in key[cid].items()},
                'review_scope':'Model screening only; not human comprehension, scientific truth or causal effect.'}
        packet['review_packet_id']=digest(json.dumps(packet,sort_keys=True).encode())
        dest=output/'masked'/(cid+'.json');write_json(dest,packet);packet_hashes[cid]=digest(dest.read_bytes())
    write_json(output/'private_key.json',key)
    write_json(output/'manifest.json',{'schema':'physwhen.writing.review.v1','packets':packet_hashes,'key_sha256':digest((output/'private_key.json').read_bytes()),'collected_path':str(Path(collected_path).resolve()),'collected_sha256':digest(Path(collected_path).read_bytes())})
    return len(cases)

def summarize_reviews(review_root, judgments_path, output):
    review_root=Path(review_root); key=json.loads((review_root/'private_key.json').read_text());manifest=json.loads((review_root/'manifest.json').read_text())
    if digest((review_root/'private_key.json').read_bytes())!=manifest['key_sha256'] or digest(Path(manifest['collected_path']).read_bytes())!=manifest['collected_sha256']:raise ValueError('review key/collected input changed')
    for cid,sha in manifest['packets'].items():
        if digest((review_root/'masked'/(cid+'.json')).read_bytes())!=sha:raise ValueError('masked review packet changed')
    judgments=read_lines(judgments_path); seen=set(); decoded=[]
    for row in judgments:
        if not isinstance(row,dict):raise ValueError('review must be an object')
        cid,alias=row.get('case_id'),row.get('alias')
        if cid not in key or alias not in key[cid] or (cid,alias) in seen:raise ValueError('invalid/duplicate review identity')
        seen.add((cid,alias));packet=json.loads((review_root/'masked'/(cid+'.json')).read_text())
        if row.get('review_packet_id')!=packet['review_packet_id']:raise ValueError('judgment belongs to another review packet')
        if row.get('fidelity') not in ('preserved','changed','uncertain'):raise ValueError('invalid fidelity judgment')
        if row.get('clarity') not in ('clear','mixed','problematic','unrated'):raise ValueError('invalid clarity judgment')
        if row.get('defect_resolution') not in ('resolved','partial','unresolved','not_applicable'):raise ValueError('invalid defect judgment')
        if row.get('unnecessary_rewrite') not in ('yes','no','uncertain'):raise ValueError('invalid rewrite judgment')
        checks=row.get('fact_checks')
        if not isinstance(checks,list) or len(checks)!=len(packet['rubric']['required_facts']):raise ValueError('incomplete fact review')
        for check,fact in zip(checks,packet['rubric']['required_facts']):
            if not isinstance(check,dict) or check.get('fact')!=fact or check.get('status') not in ('preserved','changed','uncertain'):raise ValueError('invalid fact check')
            quote=check.get('evidence_quote')
            if not isinstance(quote,str) or (quote and quote not in packet['texts'][alias]['manuscript']):raise ValueError('review evidence quote absent from manuscript')
            if check['status']=='preserved' and not quote:raise ValueError('preservation needs located evidence')
            if not isinstance(check.get('reason'),str):raise ValueError('review reason missing')
        if row['fidelity']=='preserved' and any(x['status']!='preserved' for x in checks):raise ValueError('fidelity conflicts with fact checks')
        if not isinstance(row.get('notes'),str):raise ValueError('review notes missing')
        decoded.append({**row,'arm':key[cid][alias],'mode':packet['case']['mode'],'family':packet['case']['family']})
    missing=[cid+':'+a for cid,aliases in key.items() for a in aliases if (cid,a) not in seen]
    counts={}
    for arm in ARMS:
        counts[arm]={}
        for mode in ('draft','edit'):
            subset=[r for r in decoded if r['arm']==arm and r['mode']==mode]
            counts[arm][mode]={'reviewed':len(subset),'model_fidelity_preserved':sum(r['fidelity']=='preserved' for r in subset),'model_fidelity_changed':sum(r['fidelity']=='changed' for r in subset),'model_fidelity_uncertain':sum(r['fidelity']=='uncertain' for r in subset),'model_clear_and_preserved':sum(r['fidelity']=='preserved' and r['clarity']=='clear' for r in subset),'model_unnecessary_rewrites':sum(r['unnecessary_rewrite']=='yes' for r in subset)}
    result={'schema':'physwhen.writing.model-screen.v1','counts':counts,'missing':missing,'judgments':decoded,'human_participants':0,'human_readability_effect':'not_established','interpretation':'Independent model screening only. No p-values, causal attribution, correctness certification or verified human comprehension. Changed/uncertain fidelity cannot count as a readability success.'}
    write_json(output,result);return len(decoded),len(missing)


def export_human_review(review_root, output):
    """Export optional one-version-per-case comprehension forms, not an existing reader UI."""
    review_root=Path(review_root);output=Path(output)
    if output.exists():raise ValueError('human form directory exists')
    manifest=json.loads((review_root/'manifest.json').read_text());ids=sorted(manifest['packets'])
    for form in range(3):
        rows=[];lines=['# Optional reading study — synthetic pilot materials','',
          'Read each assigned passage independently. You may do a subset. Answer in your own words; do not infer source conditions. Return the completed response template to the organizer. No automatic upload.','']
        for index,cid in enumerate(ids):
            p=review_root/'masked'/(cid+'.json')
            if digest(p.read_bytes())!=manifest['packets'][cid]:raise ValueError('review packet changed')
            packet=json.loads(p.read_text());alias=['U','V','W'][(index+form)%3]
            questions=packet['rubric']['comprehension']
            lines += [f'## {cid}', '',packet['texts'][alias]['manuscript'],'']
            for j,q in enumerate(questions,1):lines += [f'{j}. '+q['question'],'','Answer:','']
            rows.append({'case_id':cid,'review_packet_id':packet['review_packet_id'],'assigned_alias':alias,'answers':[{ 'question':q['question'],'answer':''} for q in questions],'effort':'','comment':''})
        write_json(output/f'form-{form+1}-responses.json',{'schema':'physwhen.comprehension.template.v1','form':form+1,'respondent_code':'','responses':rows,'test_mode':False,'notice':'Empty template, not collected human data. No automatic upload.'})
        dest=output/f'form-{form+1}.md';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text('\n'.join(lines)+'\n')
    return 3


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    x=sub.add_parser('validate-cases');x.add_argument('cases')
    x=sub.add_parser('freeze');x.add_argument('skill');x.add_argument('output')
    x=sub.add_parser('export');x.add_argument('--cases',required=True);x.add_argument('--protocol',required=True);x.add_argument('--baseline',required=True);x.add_argument('--candidate',required=True);x.add_argument('--freeze',required=True);x.add_argument('--rubric',required=True);x.add_argument('--output',required=True)
    x=sub.add_parser('collect');x.add_argument('--cases',required=True);x.add_argument('--jobs',required=True);x.add_argument('--responses',required=True);x.add_argument('--output',required=True)
    x=sub.add_parser('prepare-review');x.add_argument('--cases',required=True);x.add_argument('--rubric',required=True);x.add_argument('--collected',required=True);x.add_argument('--output',required=True)
    x=sub.add_parser('summarize-review');x.add_argument('--review-root',required=True);x.add_argument('--judgments',required=True);x.add_argument('--output',required=True)
    x=sub.add_parser('export-human');x.add_argument('--review-root',required=True);x.add_argument('--output',required=True)
    a=p.parse_args()
    if a.command=='validate-cases':print('valid cases:',len(validate_cases(read_lines(a.cases))))
    elif a.command=='freeze':print('frozen files:',len(freeze_candidate(a.skill,a.output)))
    elif a.command=='export':print('exported jobs:',export_jobs(a.cases,a.protocol,a.baseline,a.candidate,a.freeze,a.output,a.rubric))
    elif a.command=='collect':print('records, missing:',collect(a.cases,a.jobs,a.responses,a.output))
    elif a.command=='prepare-review':print('masked cases:',prepare_review(a.cases,a.rubric,a.collected,a.output))
    elif a.command=='summarize-review':print('judgments, missing:',summarize_reviews(a.review_root,a.judgments,a.output))
    elif a.command=='export-human':print('optional human forms:',export_human_review(a.review_root,a.output))

if __name__=='__main__':main()
