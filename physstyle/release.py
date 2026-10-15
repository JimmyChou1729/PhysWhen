"""Non-vacuous local release gates. These establish artifact integrity, not reader benefit."""
from pathlib import Path
from .common import read_json, digest
from .structure import validate_map


def check_semantic_bundle(sem, selected):
    selected=set(selected)
    assert sem['papers_full_mainbody_read']==30, 'reported paper count mismatch'
    assert len(selected)==30 and set(sem['paper_ids'])==selected and len(sem['paper_ids'])==30, 'semantic/sample identity mismatch'
    actual={p.stem:p for p in Path('data/structure/annotations').glob('*.json')}
    assert set(actual)==selected, 'actual map set mismatch'
    manifest=sem['annotation_manifest'];expected={str(p) for p in actual.values()}
    assert len(manifest)==30 and {x['path'] for x in manifest}==expected, 'annotation manifest mismatch'
    for x in manifest:assert digest(Path(x['path']).read_bytes())==x['sha256'], 'semantic report is stale'
    protocol=read_json('data/structure/protocol.json');nodes=edges=paragraphs=0
    for pid,path in actual.items():
        r=read_json(path);packet=read_json(f'data/structure/papers/{pid}.json')
        assert not validate_map(r,packet,protocol), 'invalid current map '+pid
        nodes+=len(r['nodes']);edges+=len(r['edges']);paragraphs+=len(packet['paragraphs'])
    assert nodes==sem['selected_nodes'] and edges==sem['selected_edges'] and paragraphs==sem['main_paragraphs'], 'semantic denominators stale'
    paths=[Path('reports/structure_audit_a.json'),Path('reports/structure_audit_c.json'),Path('reports/structure_audit_c2.json'),*sorted(Path('reports').glob('structure_additional_audit_*.json')),*sorted(Path('reports').glob('structure_supplement_audit_*.json'))]
    audited=set();verdicts=[];hashes=[]
    for path in paths:
        report=read_json(path);assert report, 'missing independent review'
        assert report.get('status','complete') in {'complete','completed','passed'}, 'review not complete'
        hashes.append({'path':str(path),'sha256':digest(path.read_bytes())})
        for p in report['papers']:
            pid=p['paper_id'];assert pid in selected and pid not in audited, 'unexpected/duplicate reviewed paper'
            original=read_json(f'data/structure/initial_annotations/{pid}.json');packet=read_json(f'data/structure/papers/{pid}.json')
            es=p.get('edge_reviews',p.get('edge_verdicts',[]))
            assert len(es)==len(original['edges']) and {e['edge_index'] for e in es}==set(range(len(original['edges']))), 'incomplete edge review'
            n=p.get('read_main_body_paragraphs',p.get('read_coverage',{}).get('main_body_paragraphs'))
            assert n==len(packet['paragraphs']), 'review reading coverage mismatch'
            assert all(e['verdict'] in {'agree','change','remove'} for e in es), 'invalid verdict'
            audited.add(pid);verdicts.extend(es)
    assert audited==selected, 'independent review set incomplete'
    return {'papers':len(audited),'original_edges':len(verdicts),'review_hashes':hashes}


def check_forward_bundle(prov):
    base=Path('experiments/structure_skill_v3_validation');cases={'organize':'organize.md','copyedit':'copyedit.txt','conflict':'conflict.txt','appendix':'appendix.md'}
    required={str(base/'briefs'/f'{case}.txt') for case in cases}
    required|={str(base/directory/name) for directory in ['outputs','outputs_initial'] for name in cases.values()}
    assert prov['cases']==4 and len(prov['files'])==len(required) and {x['path'] for x in prov['files']}==required, 'four required forward file sets missing'
    for x in prov['files']:assert digest(Path(x['path']).read_bytes())==x['sha256'], 'forward file hash mismatch'
    review=read_json('reports/structure_forward_review.json');extra=read_json('reports/structure_appendix_forward_review.json')
    assert review and extra and {x['case'] for x in review['cases']}=={'organize','copyedit','conflict'}, 'missing reviewed forward cases'
    assert review['summary']['scientific_contract_failures_found']==0 and not review['summary']['invented_result_or_proof_found']
    post=review['postedit'];assert all(x['status']=='passed' for x in post['fixes']) and len(post['files'])==3
    assert {x['final_path'] for x in post['files']}=={str(base/'outputs'/cases[k]) for k in ['organize','copyedit','conflict']}
    for x in post['files']:
        assert digest(Path(x['final_path']).read_bytes())==x['final_sha256'] and digest(Path(x['initial_path']).read_bytes())==x['initial_sha256']
    assert extra['status']=='complete' and extra['verdict']=='pass' and not extra['required_changes'], 'appendix review incomplete'
    assert {x['role'] for x in extra['inputs_read']}=={'brief','skill','output'}
    for x in extra['inputs_read']:assert digest(Path(x['path']).read_bytes())==x['sha256'], 'appendix review stale'
    return {'cases':4,'review_hashes':[{'path':str(path),'sha256':digest(path.read_bytes())} for path in [Path('reports/structure_forward_review.json'),Path('reports/structure_appendix_forward_review.json')]]}
