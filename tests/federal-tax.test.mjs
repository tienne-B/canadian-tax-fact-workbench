import fs from 'node:fs/promises';import assert from 'node:assert/strict';
import {loadDictionaries} from '../dist/dictionary-loader.mjs';import {makeEngine} from '../dist/engine.mjs';
const read=p=>fs.readFile(new URL('../dist/'+p,import.meta.url),'utf8');const loaded=await loadDictionaries(read),e=makeEngine(loaded.catalogue,loaded.xml);
const base={...JSON.parse(await fs.readFile(new URL('./scenarios.json',import.meta.url)))[0].inputs,'/return/taxYear':'2025','/return/currency':'CAD','/residence/status':'residentFullYear','/residence/provinceAtYearEnd':'NS','/person/birthDate':'1990-01-01'};
for(const f of loaded.catalogue.facts.filter(f=>!f.formula&&(f.path.startsWith('/ns/')||f.path.startsWith('/federalTax/')||f.module==='credits'||['/payments/taxWithheld','/payments/instalments','/specialTaxes/splitIncome','/specialTaxes/minimumTaxCarryover','/specialTaxes/oasRecovery'].includes(f.path)))){if(f.path==='/credits/basicPersonal')continue;base[f.path]=f.type==='Boolean'?false:'0';}
Object.assign(base,{'/federalTax/creditInputBasis':'creditDollars','/ns/ordinaryReturnConfirmed':true,'/ns/creditsReviewed':true,'/federalTax/ordinaryReturnConfirmed':true,'/federalTax/returnReviewed':true});
const id='33333333-3333-4333-8333-333333333333';const income=n=>({'/properties':[id],[`/properties/#${id}/net`]:String(n)});
function r(p,changes={},missing=[]){const inputs={...base,...changes};for(const k of missing)delete inputs[k];return e.result(e.build(inputs),p.startsWith('/')?p:'/federalTax/'+p);}
function expect(p,value,changes={},missing=[]){const result=r(p,changes,missing);assert.equal(result.error,undefined,p+': '+result.error);if(value===null)assert.equal(result.complete,false,p);else {assert.equal(result.complete,true,p+' '+JSON.stringify(result));assert.equal(result.value,String(value),p);}}
expect('basicPersonalBase','16129.00');
expect('basicPersonalBase','14538.00',income(253414));
expect('basicPersonalBase','15333.50',income(215648));
expect('basicPersonalBase','16452.00',{'/return/taxYear':'2026'});
expect('basicPersonalBase','14829.00',{...income(258482),'/return/taxYear':'2026'});
expect('amountOwing','0.00');expect('refund','0.00');
expect('basicPersonalCredit','2338.71'); // Exact half-up correction for the automatic personal credit.
expect('basicPersonalCredit','0.00',{'/credits/basicPersonal':'0'});
expect('basicPersonalBase','15663.76',income(199969));
expect('taxOnTaxableIncome','7279.00',income(50200));
expect('nonrefundableCredits','2338.71',income(50200));
expect('netFederalTax','4940.29',income(50200));
expect('totalPayable','9533.66',income(50200));
expect('netPayable','-466.34',{...income(50200),'/payments/taxWithheld':'10000'});
expect('refund','466.34',{...income(50200),'/payments/taxWithheld':'10000'});
expect('amountOwing','0.00',{...income(50200),'/payments/taxWithheld':'10000'});
expect('amountOwing','1533.66',{...income(50200),'/payments/taxWithheld':'8000'});
expect('refund','0.00',{...income(50200),'/payments/taxWithheld':'8000'});
expect('netPayable','0.00',{...income(50200),'/payments/taxWithheld':'9533.66'});
expect('netFederalTax','4724.72',{...income(50200),'/return/taxYear':'2026'});
expect('totalPayable','9271.51',{...income(50200),'/return/taxYear':'2026'});
expect('netFederalTax','4640.29',{...income(50200),'/credits/employment':'100','/credits/dividend':'200'});
expect('netFederalTax','0.00',{...income(10000),'/credits/donations':'10000'});
expect('netFederalTax','125.00',{'/credits/donations':'10000','/federalTax/advancedWorkersBenefit':'100','/federalTax/specialTaxes41800':'25'});
expect('netFederalTax','5000.00',{...income(50200),'/federalTax/useMinimumTaxSchedule':true,'/specialTaxes/minimumTax':'5000'});
expect('netFederalTax',null,{...income(50200),'/federalTax/useMinimumTaxSchedule':true});
expect('totalPayable','10133.66',{...income(50200),'/federalTax/cppContributionsPayable':'100','/federalTax/eiPremiumsPayable':'200','/specialTaxes/oasRecovery':'250','/federalTax/eiBenefitsRepayment':'50'});
expect('totalCreditsAndPayments','1530.00',{'/payments/taxWithheld':'1000','/payments/instalments':'200','/federalTax/workersBenefit':'300','/federalTax/provincialRefundableCredits':'30'});
expect('netFederalTax','5015.29',{...income(50200),'/credits/foreign':'100','/federalTax/investmentCreditRecapture':'200','/federalTax/loggingTaxCredit':'25'});
expect('netFederalTax','0.00',{...income(50200),'/credits/political':'650','/federalTax/investmentTaxCredit':'5000'});
for(const change of [{'/return/taxYear':'2024'},{'/return/taxYear':'2027'},{'/residence/provinceAtYearEnd':'ON'},{'/person/deathDate':'2025-12-01'},{'/federalTax/returnReviewed':false},{'/federalTax/ordinaryReturnConfirmed':false},{'/review/coreScopeApproved':false}])expect('netPayable',null,change);
for(const missing of ['/payments/taxWithheld','/payments/instalments','/credits/employment','/federalTax/cppQppOverpayment','/federalTax/returnReviewed'])expect('netPayable',null,{},[missing]);
expect('netFederalTax','4940.29',income(50200),['/ns/creditsReviewed']);
expect('netPayable',null,income(50200),['/ns/creditsReviewed']);
const packs=JSON.parse(await read('./federal-tax/parameters.json')).years;
for(const year of ['2025','2026'])for(let i=0;i<4;i++){
 const threshold=packs[year].thresholds[i];expect('taxOnTaxableIncome',packs[year].bases[i],{...income(threshold),'/return/taxYear':year});
 for(const delta of [-.01,.01]){const a=r('taxOnTaxableIncome',{...income((threshold+delta).toFixed(2)),'/return/taxYear':year});assert.equal(a.complete,true);assert.ok(Math.abs(Number(a.value)-Number(packs[year].bases[i]))<.011);}
}
assert.throws(()=>e.build({...base,'/federalTax/workersBenefit':'-1'}));
assert.throws(()=>e.build({...base,'/payments/taxWithheld':'1.001'}));
const {GraphFactory}=await import('../dist/vendor/factgraph.mjs');const g=e.build({...base,...income(50200),'/payments/taxWithheld':'10000'}),restored=GraphFactory.fromJSON(e.dictionary,g.toJSON());assert.equal(e.result(restored,'/federalTax/refund').value,'466.34');
expect('netPayable',null,{'/specialTaxes/minimumTaxCarryover':'100'});
expect('netPayable',null,{'/ns/federalAdditionalMinimumTax':'100'});
assert.equal(e.constraints({...base,'/specialTaxes/minimumTaxCarryover':'100'}).length,1);

expect('nonrefundableCredits',null,{},['/federalTax/creditInputBasis']);
const claims={'/federalTax/creditInputBasis':'claimAmounts','/credits/basicPersonal':'16000','/credits/employment':'1000','/credits/donations':'250','/credits/topUp':'25'};
expect('ordinaryClaimAmounts','17000.00',claims);
expect('ordinaryNonrefundableCredit','2465.00',claims);
expect('nonrefundableCredits','2740.00',claims);
expect('basicFederalTax','4539.00',{...income(50200),...claims});
expect('nonrefundableCredits','2655.00',{...claims,'/return/taxYear':'2026'});
expect('nonrefundableCredits','2338.71',{'/federalTax/creditInputBasis':'claimAmounts'});
console.log('PASS: federal annual brackets and BPA phase-out, credit ordering and zero floors, T691 replacement, combined NS payable, contributions and repayments, refundable credits, owing/refund/zero balance, missing-input/review/scope gates, validation and native JSON round trip.');
