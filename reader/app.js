'use strict';
const pack=window.READING_PACK,isQA=new URLSearchParams(location.search).has('qa');
const instrument='pair-preference-v1';
const key='physwhen-group-v2-'+instrument+'-'+pack.dataset_id+(isQA?'-qa':'');
const $=id=>document.getElementById(id);
document.querySelector('.tag').textContent='宇宙学阅读对照 · 批次 '+(pack.round_label||'01');
document.title='PhysWhen · 宇宙学阅读对照 · '+(pack.round_label||'01');
function randomInt(n){const a=new Uint32Array(1),limit=Math.floor(4294967296/n)*n;do{crypto.getRandomValues(a);}while(a[0]>=limit);return a[0]%n;}
function shuffled(a){a=[...a];for(let i=a.length-1;i>0;i--){const j=randomInt(i+1);[a[i],a[j]]=[a[j],a[i]];}return a;}
function newState(){const bytes=crypto.getRandomValues(new Uint8Array(16)),id=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');return {schema:'physwhen.feedback.v2',instrument,dataset_id:pack.dataset_id,participant_id:id,revision:0,test_mode:isQA,prior_exposure:'',case_order:shuffled(pack.cases.map(c=>c.id)),presentation:Object.fromEntries(pack.cases.map(c=>{const a=shuffled(['P','Q']);return [c.id,{X:a[0],Y:a[1]}];})),texts:{},comparisons:{},created_at:new Date().toISOString()};}
let state=newState(),storageOK=true;
try{const s=JSON.parse(localStorage.getItem(key));if(s?.schema===state.schema&&s.instrument===instrument&&s.dataset_id===pack.dataset_id&&s.test_mode===isQA&&/^[a-f0-9]{32}$/.test(s.participant_id)&&s.case_order?.length===3&&new Set(s.case_order).size===3&&s.case_order.every(id=>pack.cases.some(c=>c.id===id))&&s.case_order.every(id=>s.presentation?.[id]&&['P','Q'].includes(s.presentation[id].X)&&['P','Q'].includes(s.presentation[id].Y)&&s.presentation[id].X!==s.presentation[id].Y))state=s;}catch(e){storageOK=false;}
let caseIndex=state.selection?.caseIndex??0,version=state.selection?.version??'X';
if(![0,1,2].includes(caseIndex)||!['X','Y'].includes(version)){caseIndex=0;version='X';}
function paperBlocks(text){return text.replace(/^(#{1,2}[^\S\n]+[^\n]+)$/gm,'\n\n$1\n\n').trim().split(/\n\s*\n/);}
function currentCase(){return pack.cases.find(c=>c.id===state.case_order[caseIndex]);}
function comparison(){return state.comparisons[currentCase().id]??={preference:'',note:'',familiarity:''};}
function updateProgress(){$('progress').textContent=Object.values(state.comparisons).filter(t=>t.preference).length+' / 3 组已评价';}
function save(){state.selection={caseIndex,version:'X'};state.updated_at=new Date().toISOString();try{localStorage.setItem(key,JSON.stringify(state));storageOK=true;}catch(e){storageOK=false;}$('save-status').textContent=(isQA?'工程测试模式 · ':'')+(storageOK?'已保存在此浏览器；结束后请下载结果交回。':'自动保存不可用，请在离开页面前下载结果。');updateProgress();}
function renderPaper(c,version){
 const article=document.createElement('article');article.setAttribute('aria-label','版本 '+version);
 const head=document.createElement('div');head.className='article-head';
 const badge=document.createElement('h2');badge.textContent='版本 '+version;head.append(badge);article.append(head);
 const notice=document.createElement('p');notice.className='paper-notice';notice.textContent='阅读实验材料 · 基于既有研究的短论文式重述';article.append(notice);
 const title=document.createElement('h2');title.className='paper-title';title.lang='en';title.textContent=c.paper_title||'';article.append(title);
 const reading=document.createElement('div');reading.className='reading-text';reading.lang='en';article.append(reading);
 const canonical=state.presentation[c.id][version];
 paperBlocks(c.versions[canonical]).forEach(block=>{
  const heading=block.match(/^(#{1,2})\s+([^\n]+)$/);
  if(heading){if(heading[1]==='#')return;const h=document.createElement('h3');h.className='paper-section';h.textContent=heading[2];reading.append(h);return;}
  const body=document.createElement('div');body.className='reading-block';body.textContent=block;reading.append(body);
 });
 if(c.reference){const ref=document.createElement('section');ref.className='paper-reference';ref.lang='en';const h=document.createElement('h3');h.textContent='Reference';const p=document.createElement('p');p.textContent='[1] '+c.reference.authors.join(', ')+'. '+c.reference.title+'. '+c.reference.year+'. arXiv:'+c.reference.arxiv_id+'v'+c.reference.version+'.';ref.append(h,p);article.append(ref);}
 if(window.renderMathInElement)renderMathInElement(reading,{delimiters:[{left:'\\[',right:'\\]',display:true},{left:'\\(',right:'\\)',display:false},{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false,trust:false});
 return article;
}
function render(){const c=currentCase();$('participant-code').textContent=state.participant_id.slice(0,8);$('case-nav').replaceChildren();
 state.case_order.forEach((id,i)=>{const b=document.createElement('button');b.textContent=`第 ${i+1} 组`+(state.comparisons[id]?.preference?' · 已评价':'');b.setAttribute('aria-pressed',String(i===caseIndex));b.onclick=()=>{caseIndex=i;render();};$('case-nav').append(b);});
 $('case-label').textContent=`第 ${caseIndex+1} 组 · ${c.name}`;$('papers').replaceChildren(...['X','Y'].map(v=>renderPaper(c,v)));
 document.querySelectorAll('input[name="preference"]').forEach(r=>r.checked=r.value===comparison().preference);
 $('comparison-note').value=comparison().note;$('familiarity').value=comparison().familiarity;$('prior-exposure').value=state.prior_exposure;
 $('optional-feedback').open=false;$('pair-status').textContent=comparison().preference?'本组已保存，可下载结果或继续下一组。':'';
 $('next-case').textContent=caseIndex<2?'下一组（可选）':'完成，去下载结果';save();
}
$('preference').onchange=e=>{if(e.target.name!=='preference')return;comparison().preference=e.target.value;
 // An explicit pair choice records comparison completion, never invents numeric ratings.
 for(const v of ['X','Y'])state.texts[currentCase().id+':'+v]={effort:'',naturalness:'',friction:'',complete:true};
 save();$('pair-status').textContent='本组已保存，可下载结果或继续下一组。';
 const current=$('case-nav').children[caseIndex];current.textContent=`第 ${caseIndex+1} 组 · 已评价`;
};
for(const [f,k] of [['comparison-note','note'],['familiarity','familiarity']])$(f).addEventListener(f==='comparison-note'?'input':'change',()=>{comparison()[k]=$(f).value;save();});
$('prior-exposure').onchange=()=>{state.prior_exposure=$('prior-exposure').value;save();};
$('next-case').onclick=()=>{if(!comparison().preference){$('pair-status').textContent='请先选择本组偏好；两版相近或无法判断都可以。';$('preference').querySelector('input').focus();return;}
 if(caseIndex<2){caseIndex++;render();$('case-label').scrollIntoView({block:'start'});$('case-label').focus({preventScroll:true});}else{$('export-bottom').scrollIntoView({block:'center'});$('export-bottom').focus();}};
function exportText(){state.revision++;save();return JSON.stringify({...state,exported_at:new Date().toISOString()},null,2);}
function download(){const text=exportText(),a=document.createElement('a'),url=URL.createObjectURL(new Blob([text],{type:'application/json'}));a.href=url;a.download=`PhysWhen-${pack.round_label||'01'}-${isQA?'QA-':''}result-${state.participant_id.slice(0,8)}-r${state.revision}.json`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);$('export-status').textContent='已请求下载。请把结果文件私信交给邀请者；若未下载，请复制结果文本。';}
$('export').onclick=download;$('export-bottom').onclick=download;$('copy-results').onclick=()=>{$('copy-label').hidden=false;$('result-text').value=exportText();$('result-text').focus();$('result-text').select();$('export-status').textContent='请复制上方全部内容，私信交给邀请者。';};render();
