"""Source-validated exploratory paper-level discourse maps; never authorship/quality scores."""
import collections
import re
from .common import digest, read_json, summary
from .features import main_paragraphs
from .parse import strip_comments


def norm(text):
    return re.sub(r'\s+', ' ', text).strip()


def validate_map(record, packet, protocol):
    """Validate provenance, exhaustive move coverage and graph integrity, not semantics."""
    errors = []
    for key in ('paper_id', 'version', 'source_sha256', 'split'):
        if record.get(key) != packet[key]: errors.append(f'identity mismatch: {key}')
    if record.get('protocol_version') != protocol['version']: errors.append('protocol version mismatch')
    if packet['split'] != 'discovery': errors.append('semantic rule discovery requires discovery split')
    coverage = record.get('coverage', {})
    if coverage.get('main_body') != 'full_read' or coverage.get('abstract') != 'read':
        errors.append('full main-body and abstract reading not declared')
    for key in ('figures', 'appendices'):
        if not coverage.get(key): errors.append(f'missing coverage: {key}')
    ps = {p['paragraph_id']: p for p in packet['paragraphs']}
    ids = packet['main_body_paragraph_ids']; positions = {pid: i for i, pid in enumerate(ids)}
    raw = {pid: norm(''.join(strip_comments(b['raw']) for b in p['blocks'])) for pid, p in ps.items()}
    def evidence(item, where):
        if not isinstance(item, dict): errors.append(f'{where}: invalid evidence'); return
        pid = item.get('paragraph_id'); quote = item.get('exact_quote', '')
        if pid not in raw or not isinstance(quote, str) or not norm(quote) or norm(quote) not in raw.get(pid, ''):
            errors.append(f'{where}: quote not found in paragraph {pid}')
    def evidence_list(items, where, required=True):
        if not isinstance(items, list) or (required and not items): errors.append(f'{where}: missing evidence'); return
        for item in items: evidence(item, where)
    covered = []
    for i, move in enumerate(record.get('moves', [])):
        a, b = move.get('start_paragraph_id'), move.get('end_paragraph_id')
        if a not in positions or b not in positions or positions[a] > positions[b]: errors.append(f'move {i}: invalid span'); continue
        span = ids[positions[a]:positions[b]+1]; covered.extend(span)
        if move.get('role') not in protocol['move_roles']: errors.append(f'move {i}: unknown role')
        evidence_list(move.get('evidence'), f'move {i}')
        if any(e.get('paragraph_id') not in span for e in move.get('evidence', [])): errors.append(f'move {i}: evidence outside span')
    if covered != ids: errors.append('moves do not partition every main-body paragraph once in order')
    nodes = record.get('nodes', []); lookup = {n.get('id'): n for n in nodes}
    if len(lookup) != len(nodes) or None in lookup or '' in lookup: errors.append('duplicate/missing node IDs')
    for node in nodes:
        if node.get('type') not in protocol['node_types']: errors.append('invalid node type')
        if not node.get('text'): errors.append('missing node text')
        evidence_list(node.get('occurrences'), f'node {node.get("id")}')
        for occurrence in node.get('occurrences', []):
            if occurrence.get('role') not in {'preview','development','recap','qualification'}: errors.append('invalid occurrence role')
    for i, edge in enumerate(record.get('edges', [])):
        a,b = edge.get('from'),edge.get('to'); typ=edge.get('type')
        if a not in lookup or b not in lookup or a==b: errors.append(f'edge {i}: invalid endpoints'); continue
        at,bt=lookup[a]['type'],lookup[b]['type']
        allowed = {'addresses': at=='claim' and bt=='question', 'requires': bt in {'claim','method'}, 'supports': at=='evidence' and bt=='claim', 'derives_from': at in {'claim','method'} and bt=='claim', 'qualifies': at in {'premise','limitation'} and bt=='claim'}
        if typ not in protocol['edge_types'] or not allowed.get(typ): errors.append(f'edge {i}: invalid typed direction')
        if edge.get('basis') not in {'explicit','inferred','uncertain'}: errors.append(f'edge {i}: missing basis')
        if not edge.get('rationale'): errors.append(f'edge {i}: missing rationale')
        evidence_list(edge.get('evidence'), f'edge {i}')
    questions = {n['id'] for n in nodes if n.get('type')=='question'}; seen=[]
    for item in record.get('question_status', []):
        q=item.get('question_id');seen.append(q)
        if q not in questions or item.get('status') not in {'answered','open','uncertain'}: errors.append('invalid question status')
        cs=item.get('claim_ids',[])
        if any(c not in lookup or lookup[c]['type']!='claim' for c in cs): errors.append('question linked to non-claim')
        if item.get('status')=='answered' and not cs: errors.append('answered question missing claim')
        if any(not any(e.get('type')=='addresses' and e.get('from')==c and e.get('to')==q for e in record.get('edges',[])) for c in cs): errors.append('question claim missing addresses edge')
        evidence_list(item.get('evidence', []), 'question status', required=item.get('status')=='open')
    if len(seen)!=len(set(seen)) or set(seen)!=questions: errors.append('question status coverage mismatch')
    for item in record.get('recurrences', []):
        evidence(item.get('first'), 'recurrence first');evidence(item.get('second'), 'recurrence second')
        if item.get('relation') not in {'purposeful_recap','new_qualification','possible_redundancy','uncertain'}: errors.append('invalid recurrence relation')
        if not item.get('rationale'): errors.append('recurrence rationale missing')
    return errors


def map_descriptors(record, packet):
    """Selected graph descriptors with their true denominators and source locations."""
    ps=packet['paragraphs'];total=sum(p['word_count'] for p in ps);starts={};offset=0
    for p in ps: starts[p['paragraph_id']]=offset/total if total else None;offset+=p['word_count']
    nodes={n['id']:n for n in record['nodes']};staging=[]
    for n in nodes.values():
        if n['type']!='claim':continue
        role_positions={role:[starts[o['paragraph_id']] for o in n['occurrences'] if o['role']==role] for role in ['preview','development','recap','qualification']}
        staging.append({'node_id':n['id'],'positions':role_positions,'occurrences':n['occurrences']})
    order=[]
    for e in record['edges']:
        if e['type'] not in {'requires','supports','derives_from','qualifies'}:continue
        def developed(n):
            occ=[o for o in n['occurrences'] if o['role'] in {'development','qualification'}]
            return min((starts[o['paragraph_id']] for o in occ),default=None)
        a,b=developed(nodes[e['from']]),developed(nodes[e['to']])
        order.append({'from':e['from'],'to':e['to'],'type':e['type'],'basis':e['basis'],'dependent_minus_prerequisite':None if a is None or b is None else b-a,'evidence':e['evidence']})
    ids=packet['main_body_paragraph_ids'];pos={pid:i for i,pid in enumerate(ids)};role_words=collections.Counter()
    for m in record['moves']:role_words[m['role']]+=sum(p['word_count'] for p in ps[pos[m['start_paragraph_id']]:pos[m['end_paragraph_id']]+1])
    return {'paper_id':record['paper_id'],'version':record['version'],'source_sha256':record['source_sha256'],'denominators':{'main_body_paragraphs':len(ps),'main_body_prose_words':total,'selected_nodes':len(nodes),'selected_edges':len(record['edges']),'selected_questions':len(record['question_status']),'selected_recurrence_pairs':len(record['recurrences'])},'M01_question_status':dict(collections.Counter(q['status'] for q in record['question_status'])),'M02_edge_types':dict(collections.Counter(e['type'] for e in record['edges'])),'M02_edge_basis':dict(collections.Counter(e['basis'] for e in record['edges'])),'M03_claim_staging':staging,'M03_dependency_order':order,'M04_move_role_words':dict(role_words),'M04_route':[m['role'] for m in record['moves']],'M04_selected_recurrences':record['recurrences'],'limits':'Selected salient graph, not exhaustive proof/coreference; word positions exclude math tokens; negative order is not an error; inferred links are agent judgments.'}


def inventory(doc):
    """Automatic navigation inventory, explicitly not semantic argument extraction."""
    ps=main_paragraphs(doc);total=sum(p['word_count'] for p in ps);sections={};offset=0;labels={};references=[]
    for p in ps:
        sid=p['section_id']
        if sid not in sections:sections[sid]={'section_id':sid,'title':p['section_title'],'parser_role':p['section_role'],'prose_words':0,'paragraph_ids':[],'source_spans':[],'start_word_fraction':offset/total if total else None}
        s=sections[sid];s['prose_words']+=p['word_count'];s['paragraph_ids'].append(p['paragraph_id'])
        for b in p['blocks']:
            s['source_spans'].extend(b['source_spans'])
            raw=strip_comments(b['raw'])
            for match in re.finditer(r'\\label\s*\{([^{}]+)\}',raw):labels.setdefault(match[1],[]).append({'paragraph_id':p['paragraph_id'],'word_fraction':offset/total if total else None,'source_spans':b['source_spans']})
            for ref in b.get('refs',[]):references.append({'paragraph_id':p['paragraph_id'],'word_fraction':offset/total if total else None,**ref})
        offset+=p['word_count']
    for s in sections.values():s['word_share']=s['prose_words']/total if total else None
    return {'paper_id':doc['paper_id'],'version':doc['version'],'source_sha256':doc['source_sha256'],'split':doc.get('split'),'main_prose_words':total,'main_paragraphs':len(ps),'sections':list(sections.values()),'explicit_label_locations':labels,'internal_references':references,'limits':'Parser section boundaries and explicit TeX labels/references only; not semantic roles, dependencies or quality. Raw span containers can cover more than one token; unresolved references are retained.'}
