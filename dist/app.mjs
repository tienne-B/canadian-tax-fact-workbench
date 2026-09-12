import {makeEngine,canonical} from './engine.mjs';
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const label=p=>p.split('/').at(-1).replace(/([a-z0-9])([A-Z])/g,'$1 $2').replace(/([A-Z])([A-Z][a-z])/g,'$1 $2').replace(/\babil\b/i,'ABIL').replace(/\blpp\b/i,'LPP').replace(/^./,c=>c.toUpperCase());
const groups=[
 ['Return & residence',['return','person','residence'],'Choose the taxation year and record the taxpayer’s circumstances. The year does not automatically select a legal rule pack.'],
 ['Family',['dependants'],'Add the people relevant to dependency and family-based provisions.'],
 ['Income sources',['employments','businesses','properties','otherIncome'],'Add each distinct source. Use amounts classified under the Act, and count each amount only once.'],
 ['Capital gains & losses',['capital'],'Enter taxable gains and allowable losses after the relevant legal adjustments.'],
 ['Deductions',['subdivisionEDeductions','divisionCDeductions','taxableIncome'],'Record permitted deductions after eligibility, limits, and ordering have been reviewed.'],
 ['Plans & loss balances',['registeredPlans','lossBalances'],'These records describe reviewed amounts. Post them to the core income or deduction records once where appropriate.'],
 ['Credits & benefits',['credits','benefits'],'Record externally determined entitlements. These definitions do not calculate eligibility or change the core income result.'],
 ['Other tax & filing',['specialTaxes','payments','filing'],'Capture special taxes, payments, and filing determinations. A complete tax payable calculation is not part of this dictionary.'],
 ['Review & calculations',['review','income'],'Confirm the legal review of the core inputs and inspect the resulting section 3 calculation.']
];
let engine,catalogue,graph,inputs={},drafts={},errors={},step=0,selected='/taxableIncome/amount',view='interview';
const fieldId=p=>'f-'+p.replace(/[^a-zA-Z0-9]/g,'-');
function concrete(f){if(!f.path.includes('/*/'))return[f.path];const [root,suffix]=f.path.split('/*/');return(inputs[root]??[]).map(id=>`${root}/#${id}/${suffix}`);}
function dependencies(f,p){const out=[];function walk(x){if(!x)return;if(x.op==='Dependency'){let d=x.path;if(p.includes('/#')&&d.includes('/*/'))d=d.replace('/*/','/'+p.split('/')[2]+'/');if(d.includes('/*/')){const [r,s]=d.split('/*/');out.push(r,...(inputs[r]??[]).map(id=>r+'/#'+id+'/'+s));}else out.push(d);}for(const a of x.args??[])if(typeof a==='object')walk(a);}walk(f.formula);return [...new Set(out)];}
function read(p){return engine.result(graph,p);}
function money(v){if(v===null)return'Unknown';const [whole,decimal='00']=String(v).split('.');return '$'+whole.replace(/\B(?=(\d{3})+(?!\d))/g,',')+'.'+decimal.padEnd(2,'0');}
function display(p){const r=read(p),f=engine.definitions.get(canonical(p));if(!r.complete)return 'Unanswered';if(f?.type==='Dollar')return money(r.value);if(f?.type==='Boolean')return r.value==='true'?'Yes':'No';if(f?.type==='Collection')return `${inputs[p]?.length??0} records`;return r.value;}
function counts(index){const fs=catalogue.facts.filter(f=>groups[index][1].includes(f.module)&&!f.formula);const paths=fs.flatMap(concrete);return [paths.filter(p=>inputs[p]!==undefined).length,paths.length];}
function toast(text){$('#toast').textContent=text;setTimeout(()=>$('#toast').textContent='',3200);}
function update(){
 graph=engine.build(inputs);
 const constraints=engine.constraints(inputs),bad=Object.keys(errors).length;
 const notices=[...constraints,...(bad?[`${bad} field${bad===1?' has':'s have'} an invalid value. Correct the highlighted fields before exporting.`]:[])];
 $('#constraint-errors').innerHTML=notices.map(s=>`<div>${esc(s)}</div>`).join('');
 $('#provided').textContent=Object.keys(inputs).length;
 $('#fact-count').textContent=`${catalogue.facts.length} dictionary definitions`;
 const ready=read('/review/coreReady').value==='true'&&!notices.length&&inputs['/return/currency']==='CAD'&&inputs['/return/taxYear']!==undefined&&inputs['/return/ruleVersion']&&inputs['/return/sourceSnapshot'];
 const total=read('/taxableIncome/amount'),net=read('/income/netIncome');
 $('#net').textContent=!net.complete?'Awaiting inputs':ready?money(net.value):'Awaiting review';
 $('#taxable').textContent=!total.complete?'Awaiting inputs':ready?money(total.value):'Awaiting review';
 $('#review-status').textContent=ready?'Core reviewed · not total tax payable':'Review and return metadata required before use';
 $('#export').disabled=!!bad;$('#export-nodes').disabled=!!bad;
 $('#steps').innerHTML=groups.map((g,i)=>`<button data-step="${i}" class="${i===step?'active':''}" ${i===step?'aria-current="step"':''}><span class="step-index">${i+1}</span><span>${esc(g[0])}</span></button>`).join('');
 const[a,b]=counts(step);$('#section-progress').textContent=`${a} / ${b} provided`;
 document.querySelectorAll('[data-result]').forEach(el=>el.textContent=display(el.dataset.result));
 if(view==='graph')renderGraph();
}
function refs(f){return (f.authorities??[]).map(a=>`<a href="${esc(a.url)}" target="_blank" rel="noopener noreferrer">ITA ${esc(a.pinpoint)} ↗</a>`).join(' · ');}
function field(f,p){const id=fieldId(p),value=drafts[p]??inputs[p]??'',status=f.kind==='reviewed_input'?'Reviewed amount / decision':f.kind==='metadata'?'Record metadata':f.type==='Dollar'?'CAD':'',opts=f.type==='Boolean'?[['true','Yes'],['false','No']]:f.values?.map(v=>[v,label(v)]);let control;
 if(opts)control=`<select id="${id}" data-path="${esc(p)}" aria-describedby="${id}-help ${id}-error"><option value="">Unanswered</option>${opts.map(([v,t])=>`<option value="${esc(v)}" ${String(value)===v?'selected':''}>${esc(t)}</option>`).join('')}</select>`;
 else control=`<input id="${id}" data-path="${esc(p)}" type="${f.type==='Day'?'date':'text'}" ${['Dollar','Int'].includes(f.type)?'inputmode="decimal"':''} value="${esc(value)}" placeholder="${f.type==='Dollar'?'0.00 — only if confirmed':'Unanswered'}" autocomplete="off" aria-invalid="${!!errors[p]}" aria-describedby="${id}-help ${id}-error">`;
 return `<div class="field"><div class="field-header"><label for="${id}">${esc(label(f.path))}</label><span class="kind">${status}</span></div><p class="description" id="${id}-help">${esc(f.definition)}</p>${control}<div class="error" id="${id}-error">${esc(errors[p]??'')}</div><div class="field-meta">${refs(f)}</div><details><summary>Fact path${f.nonnegative?' · minimum 0':''}</summary><code>${esc(p)}</code>${f.notes?`<p class="description">${esc(f.notes)}</p>`:''}</details></div>`;
}
function collection(f){const ids=inputs[f.path],children=catalogue.facts.filter(x=>x.path.startsWith(f.path+'/*/')&&!x.formula);return `<section class="collection"><div class="collection-head"><h3>${esc(label(f.path))}</h3><span class="badge">${ids===undefined?'Unanswered':ids.length+' records'}</span></div><p class="description">${esc(f.definition)}</p><div class="collection-controls"><button data-add="${f.path}">+ Add record</button>${ids?.length?'':`<button data-empty="${f.path}">Confirm none apply</button>`}${ids!==undefined?`<button data-unset="${f.path}">Clear response</button>`:''}</div>${ids===undefined?'<p class="collection-state">No response yet. Confirm none apply if this collection is empty.</p>':ids.length?'':'<p class="collection-state">Confirmed: no records.</p>'}${(ids??[]).map((id,i)=>`<div class="record"><div class="record-title"><h3>${esc(label(f.path))} · ${i+1}</h3><button data-remove="${f.path}/#${id}">Remove record</button></div>${children.map(c=>field(c,c.path.replace('*','#'+id))).join('')}</div>`).join('')}</section>`;}
function renderStep(){
 const [name,modules,intro]=groups[step];$('#section-title').textContent=name;$('#step-number').textContent=`SECTION ${String(step+1).padStart(2,'0')}`;$('#section-intro').textContent=intro;
 $('#fields').innerHTML=modules.map(mod=>{const fs=catalogue.facts.filter(f=>f.module===mod&&!f.path.includes('/*/'));if(!fs.length)return'';return `<h3 class="group-title">${esc(label(mod))}</h3>`+fs.map(f=>f.type==='Collection'?collection(f):f.formula?`<div class="derived-row"><div><button data-inspect="${f.path}">${esc(label(f.path))} ↗</button><p class="description">Calculated fact</p></div><strong data-result="${f.path}">${esc(display(f.path))}</strong></div>`:field(f,f.path)).join('');}).join('');
 $('#previous').disabled=step===0;$('#next').textContent=step===groups.length-1?'Explore graph →':'Next section →';$('#step-position').textContent=`${step+1} of ${groups.length}`;update();
}
function chooseStep(i){step=i;setView('interview');renderStep();$('#main').scrollIntoView({behavior:'smooth',block:'start'});}
function setView(v){view=v;$('#interview').hidden=v!=='interview';$('#graph-view').hidden=v!=='graph';$('#interview-tab').setAttribute('aria-selected',v==='interview');$('#graph-tab').setAttribute('aria-selected',v==='graph');if(v==='graph')renderGraph();}
function node(p,focus=false){return `<button class="node ${read(p).complete?'complete':''} ${focus?'focus':''}" data-inspect="${esc(p)}">${esc(label(p))}<span>${esc(display(p))}</span></button>`;}
function renderGraph(){
 const paths=catalogue.facts.flatMap(concrete);if(!paths.includes(selected))selected='/taxableIncome/amount';const f=engine.definitions.get(canonical(selected));
 $('#fact-select').innerHTML=groups.map(g=>`<optgroup label="${esc(g[0])}">${paths.filter(p=>g[1].includes(engine.definitions.get(canonical(p)).module)).map(p=>`<option value="${esc(p)}" ${p===selected?'selected':''}>${esc(p)}</option>`).join('')}</optgroup>`).join('');
 const before=dependencies(f,selected),after=paths.filter(p=>dependencies(engine.definitions.get(canonical(p)),p).includes(selected));
 $('#graph-diagram').innerHTML=`<div class="graph-columns"><div class="graph-col"><small>Depends on · ${before.length}</small>${before.length?before.map(p=>node(p)).join(''):'<p class="graph-empty">Provided by you</p>'}</div><div class="graph-col"><small>Selected fact</small>${node(selected,true)}</div><div class="graph-col"><small>Used by · ${after.length}</small>${after.length?after.map(p=>node(p)).join(''):'<p class="graph-empty">No downstream expression</p>'}</div></div>`;
 $('#fact-detail').innerHTML=`<code>${esc(selected)}</code><p>${esc(f.definition)}</p><p>${f.formula?'Calculated by IRS Fact Graph. Arithmetic values shown here are for inspection; review gates still apply.':f.kind==='reviewed_input'?'This fact requires an external legal determination.':'This fact is supplied by the user.'}</p><p>${refs(f)}</p>${f.formula?`<details><summary>Calculation expression</summary><pre>${esc(JSON.stringify(f.formula,null,2))}</pre></details>`:`<button data-edit="${esc(selected)}">Edit this fact →</button>`}`;
}
function download(name,obj){const url=URL.createObjectURL(new Blob([typeof obj==='string'?obj:JSON.stringify(obj,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function confirmation(title,body,fn){$('#confirm-title').textContent=title;$('#confirm-body').textContent=body;$('#confirm-action').onclick=()=>{$('#confirm').close();fn();};$('#confirm').showModal();}
function clearCollection(p){delete inputs[p];for(const target of [inputs,drafts,errors])for(const k of Object.keys(target))if(k.startsWith(p+'/#'))delete target[k];}
function changeField(el){const p=el.dataset.path,f=engine.definitions.get(canonical(p)),raw=el.value;delete errors[p];delete drafts[p];delete inputs[p];if(raw!==''){const v=f.type==='Boolean'?raw==='true':raw;try{engine.validate(p,v);inputs[p]=v;}catch(e){drafts[p]=raw;errors[p]=e.message;}}
 el.setAttribute('aria-invalid',!!errors[p]);document.getElementById(fieldId(p)+'-error').textContent=errors[p]??'';
 try{update();}catch(e){delete inputs[p];drafts[p]=raw;errors[p]=e.message;el.setAttribute('aria-invalid','true');document.getElementById(fieldId(p)+'-error').textContent=e.message;update();}
}
async function start(){
 const [c,x]=await Promise.all([fetch('./catalogue.json').then(r=>{if(!r.ok)throw Error('Dictionary unavailable');return r.json();}),fetch('./fact-dictionary.xml').then(r=>{if(!r.ok)throw Error('XML unavailable');return r.text();})]);catalogue=c;engine=makeEngine(c,x);graph=engine.build(inputs);$('#boot').hidden=true;$('#app').hidden=false;renderStep();
 $('#steps').addEventListener('click',e=>{const b=e.target.closest('[data-step]');if(b)chooseStep(Number(b.dataset.step));});
 $('#fields').addEventListener('change',e=>{if(e.target.dataset.path)changeField(e.target);});
 $('#fields').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.add){inputs[b.dataset.add]=[...(inputs[b.dataset.add]??[]),crypto.randomUUID()];update();renderStep();}if(b.dataset.empty){inputs[b.dataset.empty]=[];update();renderStep();}if(b.dataset.unset){const p=b.dataset.unset;const action=()=>{clearCollection(p);update();renderStep();};if(inputs[p]?.length)confirmation('Clear this collection?','Its records and entered values will be removed from this tab.',action);else action();}if(b.dataset.remove){const p=b.dataset.remove;confirmation('Remove this record?','All values for this record will be removed.',()=>{const [group,id]=p.split('/#');inputs[group]=inputs[group].filter(v=>v!==id);for(const target of [inputs,drafts,errors])for(const k of Object.keys(target))if(k.startsWith(p+'/'))delete target[k];update();renderStep();});}});
 document.addEventListener('click',e=>{const b=e.target.closest('[data-inspect]');if(b){selected=b.dataset.inspect;setView('graph');}const edit=e.target.closest('[data-edit]');if(edit){const p=edit.dataset.edit;chooseStep(groups.findIndex(g=>g[1].includes(engine.definitions.get(canonical(p)).module)));document.getElementById(fieldId(p))?.focus();}});
 $('#previous').onclick=()=>chooseStep(Math.max(0,step-1));$('#next').onclick=()=>step===groups.length-1?setView('graph'):chooseStep(step+1);
 $('#interview-tab').onclick=()=>setView('interview');$('#graph-tab').onclick=()=>setView('graph');$('#fact-select').onchange=e=>{selected=e.target.value;renderGraph();};$('#cancel').onclick=()=>$('#confirm').close();
 $('#reset').onclick=()=>confirmation('Clear all answers?','Export your fact graph first if you want to keep it.',()=>{inputs={};drafts={};errors={};update();chooseStep(0);});
 $('#example').onclick=()=>confirmation('Load the worked example?','This replaces answers with fictional amounts: $60,000 remuneration, $1,200 benefits, a $1,000 employment deduction, $2,000 property income, a $5,000 business loss, and a $7,000 income deduction. Review attestations remain unanswered.',()=>{const id=crypto.randomUUID();inputs={'/return/currency':'CAD','/employments':[id],[`/employments/#${id}/remuneration`]:'60000',[`/employments/#${id}/benefits`]:'1200',[`/employments/#${id}/optionBenefits`]:'0',[`/employments/#${id}/deductions`]:'1000','/businesses':[id],[`/businesses/#${id}/net`]:'-5000','/properties':[id],[`/properties/#${id}/net`]:'2000','/otherIncome':[],'/subdivisionEDeductions':[id],[`/subdivisionEDeductions/#${id}/amount`]:'7000','/divisionCDeductions':[],'/taxableIncome/divisionCAdditions':'0','/capital/taxableGainsExcludingLpp':'0','/capital/taxableNetLppGain':'0','/capital/allowableLossesExcludingLpp':'0','/capital/abil':'0'};drafts={};errors={};update();chooseStep(2);toast('Example loaded. Inspect the graph to see $50,200 taxable income.');});
 $('#export').onclick=()=>{download('canadian-tax-fact-graph.json',graph.toJSON());toast('Exported in native IRS Fact Graph format.');};
 $('#export-nodes').onclick=()=>{const paths=catalogue.facts.flatMap(concrete);download('canadian-tax-graph-nodes.json',{format:'canadian-tax-graph',catalogueVersion:catalogue.version,exportedAt:new Date().toISOString(),coreReviewAttested:read('/review/coreReady').value==='true',constraints:engine.constraints(inputs),nodes:paths.map(p=>({path:p,type:engine.definitions.get(canonical(p)).type,...read(p)})),edges:paths.flatMap(p=>dependencies(engine.definitions.get(canonical(p)),p).map(d=>({from:d,to:p}))),inputs,nativeGraph:JSON.parse(graph.toJSON())});};
}
start().catch(e=>{$('#boot').textContent='The fact graph could not be loaded. '+e.message;console.error(e);});
