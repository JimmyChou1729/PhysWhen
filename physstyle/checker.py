"""Positioned reference comparison without authorship/readability scoring."""
import tempfile,re
from pathlib import Path
from .common import *
from .parse import parse_tex,sentences
from .features import measure

def check_file(path,profile_path='skills/physics-paper-style/profile.json'):
    path=Path(path).resolve();text=path.read_text();profile=read_json(profile_path);warnings=[];threshold=profile['reference_profiles']['D01_sentence_p90']['median']
    if path.suffix.lower() in ('.tex','.ltx') and '\\begin{document}' in text:
        with tempfile.TemporaryDirectory(prefix='physwhen-check-') as t:d=parse_tex(text.encode(),Path(t)/'source')
        d.update(paper_id='user_input',version=1,split='unassigned');m=measure(d,read_json('configs/features.json'));metrics=m['metrics'];mode='TeX parser; included companion files unavailable for standalone input'
        for p in d['paragraphs']:
            for b in p['blocks']:
                if b['kind']=='prose':
                    for sentence in sentences(b['text']):
                        if len(words(sentence))>threshold:warnings.append({'kind':'long_sentence_review','reference_threshold':threshold,'threshold_basis':'discovery median of per-paper sentence P90; review hint, not a calibrated defect threshold','path':str(path),'line_start':b['source_spans'][0]['line_start'],'word_count':len(words(sentence)),'message':'Review dependency load; this is not an error or an authorship indicator.'})
        parser_warnings=d['warnings']
    else:
        mode='plain/Markdown prose proxy; not fully comparable to source-TeX corpus'
        # Keep newlines to preserve original locations; math is removed before measuring prose.
        math_pattern=r'\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|(?<!\$)\$(?!\$).*?(?<!\$)\$(?!\$)'
        prose=re.sub(math_pattern,lambda m:'\n'*m[0].count('\n'),text,flags=re.S);pars=[s for s in re.split(r'\n\s*\n',prose) if words(s)];lens=[len(words(s)) for p in pars for s in sentences(p)];plens=[len(words(p)) for p in pars]
        metrics={'D01_sentence_median':quantile(lens,.5),'D02_paragraph_median':quantile(plens,.5)};parser_warnings=['Only sentence/paragraph prose proxies measured; equations, crossrefs and semantic features not scored.']
        line=1
        for para in re.split(r'(\n\s*\n)',prose):
            for sentence in sentences(para):
                n=len(words(sentence))
                if n>threshold:warnings.append({'kind':'long_sentence_review','reference_threshold':threshold,'threshold_basis':'discovery median of per-paper sentence P90; review hint, not a calibrated defect threshold','path':str(path),'line_start':line,'word_count':n,'mapping_type':'paragraph_container','message':'Long prose dependency span; review in context, not an automatic defect.'})
            line+=para.count('\n')
    comparisons={}
    for key,value in metrics.items():
        if key not in profile['reference_profiles']:continue
        ref=profile['reference_profiles'][key];comparisons[key]={'value':value,'discovery_papers':ref['n'],'reference_q25':ref['q25'],'reference_median':ref['median'],'reference_q75':ref['q75'],'interpretation':'descriptive_only_not_optimum'}
    return {'project':'PhysWhen','input':str(path),'measurement_mode':mode,'ai_authorship_probability':None,'human_readability_score':None,'comparisons':comparisons,'positioned_warnings':warnings,'parser_warnings':parser_warnings,'semantic_status':'host_annotation_required','content_preservation_status':'not_checked_without_frozen_fact_brief','limitations':['Short excerpts and different paragraph functions are not directly calibrated against whole-paper distributions.','No aggregate quality score, authorship detector, or demonstrated human readability improvement.']}
