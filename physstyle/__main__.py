import argparse,json,platform
from .common import *
from .pipeline import run,analyze,load_docs
from .network import Fetcher
from .corpus import discover
from .annotations import import_annotations,summarize_annotations
from .training import export_training

def main():
    p=argparse.ArgumentParser(prog='physstyle',description='PhysWhen: traceable historical physics writing profiles, never authorship probabilities.')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    x=sub.add_parser('import-feedback');x.add_argument('path')
    sub.add_parser('summarize-feedback')
    sub.add_parser('report')
    x=sub.add_parser('check');x.add_argument('--input',required=True);x.add_argument('--profile',default='skills/physics-paper-style/profile.json')
    for name in ('run','discover','analyze','export-training'):
        x=sub.add_parser(name);x.add_argument('--config',default='configs/smoke.json');x.add_argument('--resume',action='store_true');x.add_argument('--offline',action='store_true')
    x=sub.add_parser('import-annotations');x.add_argument('path')
    x=sub.add_parser('import-screening');x.add_argument('path')
    a=p.parse_args()
    if a.command=='doctor':out={'project':'PhysWhen','python':platform.python_version(),'platform':platform.platform(),'dependencies':'standard library only','network':'not tested by doctor','paid_api_enabled':False,'weight_training_enabled':False}
    elif a.command=='report':
        with corpus_lock():
            import subprocess,sys
            from .pilot import enlarged_corpus
            if not enlarged_corpus():
                subprocess.run([sys.executable,'scripts/build_artifacts.py'],check=True)
                subprocess.run([sys.executable,'scripts/stratify.py'],check=True)
            from .report import finalize_results
            out=finalize_results()
    elif a.command=='summarize-feedback':
        from .group_feedback import summarize
        out=summarize()
    elif a.command=='import-feedback':
        from .feedback import import_feedback
        out=import_feedback(a.path)
    elif a.command=='check':
        from .checker import check_file
        out=check_file(a.input,a.profile)
    elif a.command=='import-screening':
        from .corpus import import_screening
        out={'imported':import_screening(a.path)}
    elif a.command=='import-annotations':out={'imported':import_annotations(a.path),'summary':summarize_annotations()}
    else:
        cfg=read_json(a.config)
        if a.command=='run':out=run(cfg,a.offline)
        elif a.command=='analyze':out=analyze(cfg)
        elif a.command=='discover':out={'candidates':len(discover(Fetcher('data/raw/http',cfg['interval'],cfg['retries'],offline=a.offline),cfg))}
        elif a.command=='export-training':out=export_training(read_jsonl('data/manifests/corpus.jsonl'),load_docs(),cfg['seed'])
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
