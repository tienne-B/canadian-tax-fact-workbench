import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {makeEngine} from '../dist/engine.mjs';
import {loadDictionaries} from '../dist/dictionary-loader.mjs';
const read=p=>fs.readFile(new URL('../dist/'+p,import.meta.url),'utf8');
const loaded=await loadDictionaries(read),e=makeEngine(loaded.catalogue,loaded.xml);
const scenarios=JSON.parse(await fs.readFile(new URL('./scenarios.json',import.meta.url)));
const base={...scenarios[0].inputs,'/return/taxYear':'2025','/return/currency':'CAD','/residence/status':'residentFullYear','/residence/provinceAtYearEnd':'NS','/person/birthDate':'1990-01-01'};
for(const f of loaded.catalogue.facts.filter(f=>f.path.startsWith('/ns/')&&!f.formula))base[f.path]=f.type==='Boolean'?false:f.type==='Int'?'0':'0';
for(const f of loaded.catalogue.facts.filter(f=>f.path.startsWith('/review/')&&!f.formula&&f.type==='Boolean'))base[f.path]=true;
base['/ns/ordinaryReturnConfirmed']=true;base['/ns/creditsReviewed']=true;
function result(p,changes={},missing=[]){const inputs={...base,...changes};for(const k of missing)delete inputs[k];return e.result(e.build(inputs),p);}
function expect(p,v,changes={},missing=[]){const r=result(p,changes,missing);assert.equal(r.error,undefined,p+': '+r.error);if(v===null)assert.equal(r.complete,false,p);else {assert.equal(r.complete,true,p+': '+JSON.stringify(r));assert.equal(r.value,String(v),p);}}
expect('/ns/taxPayable','0.00');
console.log('Combined engine boot and zero-income tax passed.',loaded.catalogue.facts.length,'facts');
const id='22222222-2222-4222-8222-222222222222';
const income=n=>({'/properties':[id],[`/properties/#${id}/net`]:String(n)});
const packs=JSON.parse(await read('./nova-scotia/parameters.json')).years;
for(const year of ['2025','2026'])for(let i=0;i<4;i++){
 const threshold=packs[year].thresholds[i],expected=packs[year].baseTaxes[i];
 expect('/ns/bracketTax',expected,{...income(threshold),'/return/taxYear':year});
 // Adjacent cents may round one cent apart; no larger discontinuity is allowed.
 for(const delta of [-.01,.01]){const r=result('/ns/bracketTax',{...income((threshold+delta).toFixed(2)),'/return/taxYear':year});assert.equal(r.complete,true);assert.ok(Math.abs(Number(r.value)-Number(expected))<.011);}
}
expect('/ns/taxPayable','4593.37',income(50200));
expect('/ns/taxPayable','4546.79',{...income(50200),'/return/taxYear':'2026'});
expect('/ns/basicPersonalBase','11744.00',income(1000000));
expect('/ns/basicPersonalBase','11932.00',{'/return/taxYear':'2026'});
expect('/ns/spouseBase','11744.00',{'/ns/claimSpouse':true,'/person/spouseNetIncome':'0'});
expect('/ns/spouseBase','7618.00',{'/ns/claimSpouse':true,'/person/spouseNetIncome':'5000'});
expect('/ns/spouseBase','0.00',{'/ns/claimSpouse':true,'/person/spouseNetIncome':'20000'});
expect('/ns/spouseBase','11932.00',{'/return/taxYear':'2026','/ns/claimSpouse':true,'/person/spouseNetIncome':'888'});
expect('/ns/spouseBase',null,{'/ns/claimSpouse':true});
expect('/ns/ageBase','5734.00',{...income(30828),'/person/birthDate':'1960-12-31'});
expect('/ns/ageBase','0.00',{...income(30828),'/person/birthDate':'1961-01-01'});
expect('/ns/ageBase','5676.00',{...income(31828),'/person/birthDate':'1960-01-01','/return/taxYear':'2026'});
expect('/ns/ageTaxCredit','1000.00',{...income('23999.99'),'/person/birthDate':'1960-01-01'});
expect('/ns/ageTaxCredit','0.00',{...income(24000),'/person/birthDate':'1960-01-01'});
expect('/ns/donationCredit','185.58',{'/ns/eligibleDonations':'1000'});
expect('/ns/dividendCredit','103.50',{'/ns/taxableEligibleDividends':'1000','/ns/taxableOtherDividends':'1000'});
expect('/ns/pensionBase','1173.00',{'/ns/eligiblePensionIncome':'5000'});
expect('/ns/medicalBase','1363.00',{...income(60000),'/ns/eligibleMedicalExpenses':'3000'});
expect('/ns/medicalBase','100.00',{...income(10000),'/ns/eligibleMedicalExpenses':'400'});
expect('/ns/lowIncomeReduction','680.00',{'/ns/claimLowIncomeReduction':true,'/ns/adjustedFamilyIncome':'20000','/ns/qualifyingSpouseOrDependant':true,'/ns/otherQualifyingDependants':'2'});
expect('/ns/lowIncomeReduction','0.00',{'/ns/claimLowIncomeReduction':false},['/ns/adjustedFamilyIncome','/ns/qualifyingSpouseOrDependant','/ns/otherQualifyingDependants']);
expect('/ns/lowIncomeReduction',null,{'/ns/claimLowIncomeReduction':true},['/ns/adjustedFamilyIncome']);
expect('/ns/politicalCredit','750.00',{'/ns/politicalContributions':'5000'});
expect('/ns/farmerFoodCredit','250.00',{'/ns/farmerFoodDonations':'1000'});
expect('/ns/taxPayable','0.00',{...income(20000),'/ns/certificateCredits':'10000'});
expect('/ns/taxBeforeReduction','575.00',{'/ns/federalAdditionalMinimumTax':'1000'});
expect('/ns/taxBeforeReduction','4493.37',{...income(50200),'/ns/foreignTaxCredit':'100'});
for(const change of [{'/return/taxYear':'2024'},{'/return/taxYear':'2027'},{'/residence/provinceAtYearEnd':'ON'},{'/residence/status':'nonResident'},{'/person/deathDate':'2025-12-01'},{'/ns/ordinaryReturnConfirmed':false},{'/ns/creditsReviewed':false},{'/review/coreScopeApproved':false},{'/ns/claimSpouse':true,'/person/spouseNetIncome':'0','/ns/eligibleDependantBase':'1'},{'/ns/eligibleDependantBase':'11745'},{'/ns/farmerFoodDonations':'1'}])expect('/ns/taxPayable',null,change);
for(const missing of ['/ns/eligibleDonations','/ns/certificateCredits','/ns/claimSpouse','/return/taxYear','/ns/creditsReviewed','/person/birthDate'])expect('/ns/taxPayable',null,{},[missing]);
assert.throws(()=>e.build({...base,'/ns/otherQualifyingDependants':'-1'}));
assert.throws(()=>e.build({...base,'/ns/eligibleDonations':'1.001'}));
const {GraphFactory}=await import('../dist/vendor/factgraph.mjs');
const g=e.build({...base,...income(50200)}), restored=GraphFactory.fromJSON(e.dictionary,g.toJSON());
assert.equal(e.result(restored,'/ns/taxPayable').value,'4593.37');
assert.equal(e.result(e.build({...base,...income(60200)}),'/ns/taxPayable').value,'6088.37');
const manifests=JSON.parse(await read('./dictionary-modules.json'));
await assert.rejects(()=>loadDictionaries(p=>p==='./dictionary-modules.json'?Promise.resolve(JSON.stringify({...manifests,modules:[...manifests.modules,manifests.modules[0]]})):read(p)),/Duplicate dictionary module/);
console.log('PASS: NS 2025/2026 brackets and adjacent cents; shared federal income updates; personal, spouse, age, pension, medical, donation, dividend, low-income, political, food and minimum-tax calculations; scope/review/consistency gates; unknown inputs; validation; module duplication; native graph round trip.');
