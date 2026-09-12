import fs from 'node:fs';import assert from 'node:assert/strict';import {makeEngine} from '../dist/engine.mjs';
const e=makeEngine(JSON.parse(fs.readFileSync(new URL('../dist/catalogue.json',import.meta.url))),fs.readFileSync(new URL('../dist/fact-dictionary.xml',import.meta.url),'utf8'));
const scenarios=JSON.parse(fs.readFileSync(new URL('./scenarios.json',import.meta.url)));
for(const s of scenarios){const inputs={...(s.inherit_zero?scenarios[0].inputs:{}),...s.inputs};for(const p of s.remove??[])delete inputs[p];const g=e.build(inputs);for(const[p,v]of Object.entries(s.expected)){const r=e.result(g,p);assert.equal(r.error,undefined);if(v==='MISSING')assert.equal(r.complete,false,s.name+' '+p);else{assert.equal(r.complete,true,s.name+' '+p);assert.equal(r.value,typeof v==='boolean'?String(v):Number(v).toFixed(2),s.name+' '+p);}}}
for(const[p,v]of [['/capital/abil','-1'],['/capital/abil','1.001'],['/person/birthDate','2026-02-30'],['/return/taxYear','2026.5'],['/return/currency','USD'],['/review/coreScopeApproved','true'],['/income/netIncome','20']])assert.throws(()=>e.build({[p]:v}),p);
assert.equal(e.constraints({'/capital/abil':'10','/capital/allowableLossesExcludingLpp':'9.99'}).length,1);
assert.equal(e.constraints({'/capital/abil':'9.99','/capital/allowableLossesExcludingLpp':'10'}).length,0);
const unknown=e.build({});assert.equal(e.result(unknown,'/income/netIncome').complete,false);
const explicit=e.build({'/employments':[]});assert.equal(e.result(explicit,'/income/employmentsIncome').value,'0.00');
const {GraphFactory}=await import('../dist/vendor/factgraph.mjs');const roundtrip=GraphFactory.fromJSON(e.dictionary,explicit.toJSON());assert.equal(e.result(roundtrip,'/income/employmentsIncome').value,'0.00');
console.log('PASS: 11 native IRS-engine scenarios; invalid-input validation; ABIL consistency; unknown versus empty collection; native JSON round trip.');
