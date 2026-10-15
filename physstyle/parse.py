"""Non-executing bounded TeX parser. Raw bytes, math, ordered blocks and source lines survive."""
import bisect, gzip, io, re, tarfile, zipfile
from pathlib import Path
from .common import *
MAX_EXPANDED=100*1024**2
MATH_ENVS={'equation','equation*','align','align*','eqnarray','eqnarray*','gather','gather*','multline','multline*','displaymath','flalign','flalign*','alignat','alignat*','empheq'}
SKIP_ENVS={'thebibliography','references','acknowledgments','acknowledgements','figure','figure*','table','table*','verbatim','comment','filecontents','filecontents*'}
TEXT_CMDS={'textit','textbf','textrm','textsf','texttt','emph','underline','mbox','hbox','text','mathrm','footnotesize','small','normalfont','bf','it','rm','sc','sl','em','noindent','nonumber','notag','protect','relax','ignorespaces','newline','linebreak','vspace','hspace','centering','raggedright','item'}
DROP_ARGS={'cite','citep','citet','citealt','citealp','onlinecite','bibliography','bibliographystyle','label','index','footnote','footnotetext','thanks','url','href','includegraphics','vspace','hspace','phantom','hphantom','vphantom','color','textcolor'}

def extract_source(blob,dest):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True);files=[]
    def accept(name,b):
        p=safe_child(dest,name)
        if p.suffix.lower() not in {'.tex','.ltx','.sty','.cls','.bbl','.bib','.txt',''}:return
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);files.append(p)
    if blob[:2]==b'\x1f\x8b':
        with gzip.GzipFile(fileobj=io.BytesIO(blob)) as f:blob=f.read(MAX_EXPANDED+1)
        if len(blob)>MAX_EXPANDED:raise ValueError('expanded size limit')
    total=0
    if zipfile.is_zipfile(io.BytesIO(blob)):
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            if len(z.infolist())>2000:raise ValueError('archive file count')
            for m in z.infolist():
                safe_child(dest,m.filename)
                if (m.external_attr>>16)&0o170000==0o120000:raise ValueError('archive symlink')
                total+=m.file_size
                if total>MAX_EXPANDED:raise ValueError('expanded size limit')
            for m in z.infolist():
                if not m.is_dir():accept(m.filename,z.read(m))
    else:
        try:tf=tarfile.open(fileobj=io.BytesIO(blob),mode='r:')
        except tarfile.ReadError:
            if blob.startswith(b'%PDF'):raise ValueError('PDF source: not safely parsed by TeX route')
            if len(blob)>MAX_EXPANDED:raise ValueError('expanded size limit')
            accept('main.tex',blob);return files
        with tf:
            members=tf.getmembers()
            if len(members)>2000:raise ValueError('archive file count')
            for m in members:
                safe_child(dest,m.name)
                if not (m.isfile() or m.isdir()):raise ValueError('archive link or special file')
                total+=m.size
                if total>MAX_EXPANDED:raise ValueError('expanded size limit')
            for m in members:
                if m.isfile():accept(m.name,tf.extractfile(m).read())
    return files

def strip_comments(s):return re.sub(r'(?<!\\)%[^\n]*',lambda m:'⁠'+' '*(len(m[0])-1),s)
def group(s,i,opening='{',closing='}'):
    if i>=len(s) or s[i]!=opening:return '',i
    depth=1;j=i+1
    while j<len(s):
        if s[j]=='\\':j+=2;continue
        if s[j]==opening:depth+=1
        if s[j]==closing:
            depth-=1
            if depth==0:return s[i+1:j],j+1
        j+=1
    return s[i+1:],len(s)
def arguments(s,i):
    while i<len(s) and s[i].isspace():i+=1
    if i<len(s) and s[i]=='*':i+=1
    while i<len(s) and s[i]=='[':
        _,i=group(s,i,'[',']')
        while i<len(s) and s[i].isspace():i+=1
    return group(s,i)

def flatten(root,main):
    lines=[];origins=[];warnings=[];seen=[]
    def visit(p,depth=0):
        p=p.resolve()
        if not p.is_relative_to(root.resolve()):raise ValueError('include path escape')
        if depth>15 or p in seen:raise ValueError('include cycle/depth')
        seen.append(p)
        for n,line in enumerate(p.read_text(errors='replace').splitlines(True),1):
            clean=strip_comments(line)
            m=re.fullmatch(r'\s*\\(?:input|include)\s*\{([^}]+)\}\s*',clean.replace('\u2060',' '))
            if m:
                rel=m[1];q=safe_child(p.parent,rel if Path(rel).suffix else rel+'.tex')
                if not q.is_relative_to(root.resolve()):raise ValueError('include path escape')
                if q.exists():visit(q,depth+1)
                else:warnings.append('missing_include:'+rel)
            else:
                if re.search(r'\\(?:input|include)\b',clean):warnings.append('inline_include_unexpanded')
                lines.append(line if line.endswith('\n') else line+'\n');origins.append({'source_file':str(p.relative_to(root)),'line':n})
        seen.pop()
    visit(main)
    return ''.join(lines),origins,warnings

def sentences(s):
    # Preserve common physics abbreviations and initials; conservative deterministic v1.
    s=re.sub(r'\b(Eq|Eqs|Fig|Figs|Sec|Secs|Ref|Refs|Dr|Prof|cf|vs|i\.e|e\.g)\.',lambda m:m[0].replace('.','∯'),s)
    s=s.replace('et al.','et al∯')
    s=re.sub(r'\b([A-Z])\.(?=\s+[A-Z])',r'\1∯',s)
    return [x.strip().replace('∯','.') for x in re.split(r'(?<=[.!?])\s+(?=[A-Z(])',s) if words(x)]

def normalize(s,macros=None):
    s=s.replace('⁠',' ');macros=macros or {};unknown=[];out=[];i=0
    while i<len(s):
        if s[i]=='\\':
            m=re.match(r'\\([A-Za-z@]+|.)',s[i:],re.S)
            if not m:i+=1;continue
            cmd=m[1];i+=len(m[0])
            if cmd in ('ref','eqref','autoref','cref','Cref','pageref'):
                _,i=arguments(s,i);out.append(' [REF] ');continue
            if cmd in DROP_ARGS:
                _,i=arguments(s,i);out.append(' ');continue
            if cmd in macros and '\\' not in macros[cmd] and '#' not in macros[cmd]:out.append(macros[cmd]);continue
            if cmd in TEXT_CMDS:out.append(' ');continue
            if cmd in ('begin','end'):
                _,i=arguments(s,i);continue
            if cmd in ('%','&','_','#','$'):out.append(' ');continue
            if not cmd.isalpha():out.append(' ');continue
            unknown.append(cmd);out.append(' [MACRO] ')
        else:
            out.append(' ' if s[i] in '{}~&' else s[i]);i+=1
    return re.sub(r'\s+',' ',''.join(out)).strip(),sorted(set(unknown))

def role(title,appendix=False):
    if appendix or re.search(r'\bappendix\b',title,re.I):return 'appendix'
    t=title.lower()
    if 'abstract' in t:return 'abstract'
    if re.search(r'introduction|motivation',t):return 'introduction'
    if re.search(r'conclu|discussion|summary|outlook',t):return 'discussion_conclusion'
    return 'technical_body' if title else 'frontmatter'

def parse_tex(blob,root):
    root=Path(root).resolve();files=extract_source(blob,root)
    mains=[p for p in files if p.suffix in ('.tex','.ltx','') and '\\begin{document}' in strip_comments(p.read_text(errors='replace'))]
    if not mains:raise ValueError('no TeX main with document boundary')
    main=max(mains,key=lambda p:p.stat().st_size)
    raw,origins,warnings=flatten(root,main);s=strip_comments(raw)
    if len(mains)>1:warnings.append('multiple_main_candidates_largest_selected')
    starts=[0]+[m.end() for m in re.finditer('\n',raw)]
    def span(a,b):
        indexes=range(bisect.bisect_right(starts,a)-1,bisect.bisect_right(starts,max(a,b-1)))
        result=[]
        for idx in indexes:
            if idx>=len(origins):continue
            o=origins[idx]
            if result and result[-1]['source_file']==o['source_file'] and result[-1]['line_end']+1==o['line']:result[-1]['line_end']=o['line']
            else:result.append({'source_file':o['source_file'],'line_start':o['line'],'line_end':o['line'],'mapping_type':'source_lines'})
        return result
    macros={};macro_args={}
    definition_text=s+'\n'+'\n'.join(strip_comments(p.read_text(errors='replace')) for p in files if p.suffix=='.sty')
    def_aliases=re.findall(r'\\(?:let|def)\s*\\([A-Za-z]+)\s*(?:\{)?\\newcommand',definition_text)
    def_aliases+=re.findall(r'\\newcommand\s*\{\\([A-Za-z]+)\}\s*\{\\newcommand\}',definition_text)
    for alias in def_aliases:definition_text=re.sub(r'\\'+re.escape(alias)+r'\b',lambda m:'\\newcommand',definition_text)
    pattern=r'\\(?:newcommand|renewcommand|providecommand)\*?\s*(?:\{\\([A-Za-z]+)\}|\\([A-Za-z]+))\s*(?:\[(\d)\])?\s*(\{)|\\def\s*\\([A-Za-z]+)\s*(\{)'
    for m in re.finditer(pattern,definition_text):
        name=m[1] or m[2] or m[5];val,_=group(definition_text,m.end()-1);macros[name]=val;macro_args[name]=int(m[3] or 0)
    # Expand only bounded zero-argument macro aliases as data; never execute TeX.
    for _ in range(8):
        changed=False
        for k,v in list(macros.items()):
            if re.fullmatch(r'\\[A-Za-z]+',v) and v[1:] in macros and v[1:]!=k:
                macros[k]=macros[v[1:]];changed=True
        if not changed:break
    for _ in range(8):
        changed=False
        for k,v in list(macros.items()):
            if macro_args.get(k) or '#' in v:continue
            def expand_alias(m):
                replacement=macros.get(m[1],'')
                if m[1]!=k and len(replacement)<2048 and '#' not in replacement and re.search(r'\\(?:begin|end)\{(?:equation\*?|eqnarray\*?|align\*?)\}',replacement):return replacement
                return m[0]
            expanded=re.sub(r'\\([A-Za-z]+)',expand_alias,v)
            if len(expanded)<=4096 and expanded!=v:macros[k]=expanded;changed=True
        if not changed:break
    aliases={k:v for k,v in macros.items() if re.search(r'\\(?:begin|end)\{(?:equation\*?|align\*?|eqnarray\*?)\}',v)}
    begin=s.find('\\begin{document}')+len('\\begin{document}');end=s.find('\\end{document}',begin);end=len(s) if end<0 else end
    paragraphs=[];sections=[];blocks=[];title='';section_id='s0';appendix=False;cursor=begin;i=begin
    def add(kind,a,b,extra=None):
        if b<=a or (kind=='prose' and not s[a:b].strip()):return
        d={'kind':kind,'raw':raw[a:b],'source_spans':span(a,b),'flat_start':a,'flat_end':b}
        if kind=='prose':
            d['text'],d['unknown_macros']=normalize(s[a:b],macros)
            d['text']=d['text'].replace('[REF]',' ').replace('[MACRO]',' ')
            d['sentences']=sentences(d['text']);d['word_count']=len(words(d['text']))
            d['refs']=[{'tex':m[0],'source_spans':span(a+m.start(),a+m.end())} for m in re.finditer(r'\\(?:eqref|ref|autoref|cref|Cref|pageref)\s*\{[^}]+\}',s[a:b])]
        if extra:d.update(extra)
        blocks.append(d)
    def finish():
        nonlocal blocks
        if not blocks:return
        if any(x['kind'] in ('display_math','inline_math') or x.get('word_count',0)>0 for x in blocks):
            pid=f'p{len(paragraphs):04d}'
            for j,b in enumerate(blocks):b['block_id']=f'{pid}:b{j}'
            paragraph_role=role(title,appendix)
            prose_start=' '.join(b.get('text','') for b in blocks).strip()
            # Unsectioned letters sometimes place a funding/thanks paragraph before
            # the bibliography without an acknowledgment command. Retain its source
            # position, but exclude these explicit paragraph-opening cues from body.
            if title=='Unsectioned body' and re.match(r'^(?:Acknowledg(?:e)?ments?\b|(?:I|We)\s+(?:(?:wish|would like)\s+to\s+)?thank\b|This\s+(?:work|research)\s+(?:was|is|has been)\s+(?:funded\b|supported\b.{0,100}\b(?:grant|foundation|council|department|university|program|programme)\b))',prose_start,re.I):
                paragraph_role='acknowledgments';warnings.append('excluded_unsectioned_acknowledgment_paragraph')
            paragraphs.append({'paragraph_id':pid,'section_id':section_id,'section_title':title,'section_role':paragraph_role,'blocks':blocks,'word_count':sum(b.get('word_count',0) for b in blocks)})
        blocks=[]
    while i<end:
        # Blank lines are TeX paragraph boundaries; blanks inside math are consumed as one block.
        blank=re.match(r'\n[ \t]*\n(?:[ \t]*\n)*',s[i:])
        if blank:
            add('prose',cursor,i);finish();i+=len(blank[0]);cursor=i;continue
        if s[i]=='$' and (i==0 or s[i-1]!='\\'):
            delimiter='$$' if s.startswith('$$',i) else '$';j=i+len(delimiter)
            while j<end:
                if s.startswith(delimiter,j) and s[j-1]!='\\':break
                j+=1
            add('prose',cursor,i);j=min(end,j+len(delimiter));add('display_math' if delimiter=='$$' else 'inline_math',i,j);i=j;cursor=i;continue
        if s[i]=='\\':
            m=re.match(r'\\([A-Za-z@]+|.)',s[i:],re.S);cmd=m[1];after=i+len(m[0])
            if cmd in ('[','('):
                close='\\]' if cmd=='[' else '\\)';j=s.find(close,after)
                if j<0:warnings.append('unclosed_math');j=end-len(close)
                j+=len(close);add('prose',cursor,i);add('display_math' if cmd=='[' else 'inline_math',i,j);i=j;cursor=i;continue
            if cmd=='appendix':
                add('prose',cursor,i);finish();appendix=True;i=after;cursor=i;continue
            if cmd in ('section','subsection','subsubsection','chapter'):
                t,j=arguments(s,after);add('prose',cursor,i);finish();title=normalize(t,macros)[0];section_id=f's{len(sections)+1}'
                if re.search('acknowledg|references|bibliography',title,re.I):
                    # Skip acknowledgements, then resume at the next structural section.
                    nxt=re.search(r'\\(?:appendix|section|subsection|end\{document\})',s[j:])
                    i=j+nxt.start() if nxt else end;cursor=i;continue
                sections.append({'section_id':section_id,'title':title,'role':role(title,appendix),'source_spans':span(i,j)});i=j;cursor=i;continue
            if cmd in ('acknowledgments','acknowledgements','Acknowledgements','Acknowledgments'):
                add('prose',cursor,i);finish();nxt=re.search(r'\\(?:appendix|section|bibliography|begin\{thebibliography\}|end\{document\})',s[after:]);i=after+nxt.start() if nxt else end;cursor=i;continue
            if cmd in ('newcommand','renewcommand','providecommand','def') or cmd in def_aliases:
                add('prose',cursor,i);mdef=re.match(r'\s*(?:\{\\[A-Za-z]+\}|\\[A-Za-z]+)\s*(?:\[\d\])?\s*',s[after:]);j=after+len(mdef[0]) if mdef else after;_,j=group(s,j);i=j;cursor=i;continue
            if cmd in ('bibliography','printbibliography'):add('prose',cursor,i);finish();break
            if cmd=='par':add('prose',cursor,i);finish();i=after;cursor=i;continue
            if cmd in ('maketitle','tableofcontents'):
                add('prose',cursor,i);i=after;cursor=i;continue
            if cmd in ('title','author','affiliation','address','date','email','keywords','pacs','preprint'):
                add('prose',cursor,i);_,j=arguments(s,after);i=j;cursor=i;continue
            if cmd in ('footnote','footnotetext','thanks'):
                add('prose',cursor,i);_,j=arguments(s,after);warnings.append('excluded_footnote');i=j;cursor=i;continue
            alias=aliases.get(cmd)
            if alias and 0<macro_args.get(cmd,0)<=3 and '#1' in alias and '\\end{' in alias:
                j=after
                for _ in range(macro_args[cmd]):_,j=arguments(s,j)
                add('prose',cursor,i);add('display_math',i,j,{'environment':'macro:'+cmd,'labels':re.findall(r'\\label\{([^}]+)\}',s[i:j])});i=j;cursor=i;continue
            if cmd=='begin' or (alias and alias.startswith('\\begin')):
                env,j=arguments(s,after) if cmd=='begin' else (re.search(r'\{([^}]+)\}',alias)[1],after)
                if env in ('appendix','appendices'):
                    add('prose',cursor,i);finish();appendix=True;i=j;cursor=i;continue
                if env in MATH_ENVS|SKIP_ENVS:
                    close='\\end{'+env+'}';k=s.find(close,j);closing_len=len(close)
                    if alias:
                        ends=[k for k,v in aliases.items() if close in v and not v.startswith('\\begin')]
                        if ends:
                            am=re.search(r'\\(?:'+'|'.join(map(re.escape,ends))+r')\b',s[j:])
                            if am:k=j+am.start();closing_len=len(am[0])
                    if k<0:warnings.append('unclosed_environment:'+env);k=end;closing_len=0
                    add('prose',cursor,i)
                    if env in MATH_ENVS:add('display_math',i,k+closing_len,{'environment':env,'labels':re.findall(r'\\label\{([^}]+)\}',s[i:k])})
                    else:warnings.append('excluded_environment:'+env)
                    i=k+closing_len;cursor=i
                    if env in ('thebibliography','references'):finish();break
                    continue
                if env.lower()=='abstract':
                    add('prose',cursor,i);finish();title='Abstract';section_id='abstract';i=j;cursor=i;continue
            if cmd=='end':
                env,j=arguments(s,after)
                if env.lower()=='abstract':
                    add('prose',cursor,i);finish();title='' if re.search(r'\\(?:section|chapter)\b',s[begin:end]) else 'Unsectioned body';section_id='s0';i=j;cursor=i;continue
            i=after;continue
        i+=1
    if i>=end:add('prose',cursor,end);finish()
    prose=' '.join(b.get('text','') for p in paragraphs if p['section_role'] not in ('appendix','abstract','frontmatter','acknowledgments') for b in p['blocks'])
    unknown=sorted({c for p in paragraphs for b in p['blocks'] for c in b.get('unknown_macros',[])})
    return {'parser_version':'tex-struct-v1','main_file':str(main.relative_to(root)),'source_root':str(root),'source_files':{str(p.relative_to(root)):digest(p.read_bytes()) for p in files},'sections':sections,'paragraphs':paragraphs,'warnings':sorted(set(warnings)),'unknown_macros':unknown,'main_prose_words':len(words(prose)),'normalized_body_sha256':digest(prose.encode()),'usable':len(words(prose))>=500,'position_contract':'Raw source line spans are authoritative; normalized sentences map to containing prose block, not exact source characters.'}
