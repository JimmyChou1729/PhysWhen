"""Check optional outline ledger integrity. Standard library only; no quality score."""
import argparse,json,sys

def check(data):
    errors=[];hints=[];groups={};all_ids=set()
    for name in ['questions','claims','evidence','conditions','sections','deferred_material']:
        entries=data.get(name,[])
        if not isinstance(entries,list):errors.append(name+': expected list');entries=[]
        groups[name]={}
        for item in entries:
            if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not item['id']:
                errors.append(name+': invalid item/id');continue
            if item['id'] in all_ids:errors.append('duplicate id: '+item['id'])
            all_ids.add(item['id']);groups[name][item['id']]=item
    def refs(item,key,group):
        values=item.get(key,[])
        if not isinstance(values,list) or any(not isinstance(v,str) for v in values):errors.append(item['id']+': invalid '+key);return []
        for value in values:
            if value not in groups[group]:errors.append(item['id']+': unknown '+key+' '+value)
        return values
    for q in groups['questions'].values():
        cs=refs(q,'claim_ids','claims')
        if q.get('status') not in ['answered','open','uncertain']:errors.append(q['id']+': invalid question status')
        if q.get('status')=='answered' and not cs:errors.append(q['id']+': answered without claim')
    for c in groups['claims'].values():
        es=refs(c,'evidence_ids','evidence');refs(c,'condition_ids','conditions')
        if c.get('status') not in ['supported','proposed','open']:errors.append(c['id']+': invalid claim status')
        if c.get('status')=='supported' and not es:errors.append(c['id']+': supported without identified evidence')
    placed={k:set() for k in ['claims','evidence','conditions']}
    for section in groups['sections'].values():
        if not section.get('purpose'):errors.append(section['id']+': missing purpose')
        for key,group in [('claim_ids','claims'),('evidence_ids','evidence'),('condition_ids','conditions')]:placed[group].update(refs(section,key,group))
    for group in placed:
        for value in set(groups[group])-placed[group]:errors.append(value+': absent from section plan')
    endpoints=set(groups['claims'])|set(groups['evidence'])|set(groups['conditions'])
    for edge in data.get('dependencies',[]):
        if not isinstance(edge,dict) or edge.get('from') not in endpoints or edge.get('to') not in endpoints or edge.get('from')==edge.get('to'):errors.append('invalid dependency endpoints')
    for item in groups['deferred_material'].values():
        if not item.get('reason') or not item.get('destination') or not isinstance(item.get('available'),bool):errors.append(item['id']+': incomplete deferral record')
        elif not item['available']:hints.append(item['id']+': deferred material is not yet written; do not claim it supplies a proof')
    return {'status':'fail' if errors else 'pass','errors':errors,'review_hints':hints,'limits':'Integrity only. Does not evaluate scientific support, completeness, organization quality or readability.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('path');args=parser.parse_args()
    try:
        with open(args.path) as f:result=check(json.load(f))
    except (OSError,ValueError,TypeError) as exc:result={'status':'fail','errors':[str(exc)]}
    print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(result['status']=='fail')
