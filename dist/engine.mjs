import {FactDictionaryFactory, GraphFactory} from './vendor/factgraph.mjs';
export const canonical=p=>p.replace(/\/#[^/]+/g,'/*');
export function makeEngine(catalogue,xml){
 const definitions=new Map(catalogue.facts.map(f=>[f.path,f]));
 const dictionary=FactDictionaryFactory.importFromXml(xml);
 function validate(path,v){
  const f=definitions.get(canonical(path));
  if(!f||f.formula)throw Error('Unknown or calculated fact: '+path);
  if(f.type==='Collection'){
   if(!Array.isArray(v)||new Set(v).size!==v.length||v.some(x=>! /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(x)))throw Error('Invalid collection');
  }else if(f.type==='Dollar'){
   if(typeof v!=='string'||! /^-?\d+(?:\.\d{1,2})?$/.test(v))throw Error('Enter a dollar amount with at most two decimal places.');
   if(f.nonnegative&&Number(v)<0)throw Error('This amount must be zero or greater.');
  }else if(f.type==='Int'){
   if(! /^-?\d+$/.test(String(v))||Number(v)<-2147483648||Number(v)>2147483647)throw Error('Enter a whole number.');
   if(path==='/return/taxYear'&&(Number(v)<1900||Number(v)>2200))throw Error('Enter a year from 1900 to 2200.');
  }else if(f.type==='Boolean'&&typeof v!=='boolean')throw Error('Choose yes or no.');
  else if(f.type==='Day'&&(! /^\d{4}-\d{2}-\d{2}$/.test(v)||!Number.isFinite(Date.parse(v))||new Date(v).toISOString().slice(0,10)!==v))throw Error('Enter a valid date.');
  else if(f.type==='String'&&typeof v!=='string')throw Error('Enter text.');
  if(f.minimum!==undefined&&Number(v)<f.minimum)throw Error('Minimum value is '+f.minimum);
  if(f.values&&!f.values.includes(v))throw Error('Choose one of the available options.');
 }
 function build(inputs){
  const graph=GraphFactory.apply(dictionary);
  for(const [p,v]of Object.entries(inputs))validate(p,v);
  for(const[p,v]of Object.entries(inputs).filter(([p])=>definitions.get(canonical(p)).type==='Collection')){
   if(!v.length)graph.removeFromCollection(p,'00000000-0000-4000-8000-000000000000');
   else for(const id of v)graph.addToCollection(p,id);
  }
  for(const[p,v]of Object.entries(inputs)){
   if(definitions.get(canonical(p)).type==='Collection')continue;
   if(p.includes('/#')){const [group,member]=p.split('/#');if(!inputs[group]?.includes(member.split('/')[0]))throw Error('Record is not in its collection.');}
   const r=graph.set(p,String(v));if(r?.errorType)throw Error(p+': '+(r.errorName||r.errorType));
  }
  return graph;
 }
 function result(graph,p){
  try{const r=graph.get(p);return {complete:r.complete,value:r.hasValue?String(r.get):null};}catch(e){return {complete:false,value:null,error:e.message};}
 }
 function constraints(inputs){
  const errors=[];
  const a=inputs['/capital/abil'],b=inputs['/capital/allowableLossesExcludingLpp'];
  const cents=x=>BigInt(x.replace('.','')+'0'.repeat(2-(x.split('.')[1]?.length??0)));
  if(a!==undefined&&b!==undefined&&cents(a)>cents(b))errors.push('ABIL must not exceed allowable losses excluding listed personal property.');
  if(inputs['/residence/status']&&inputs['/residence/status']!=='residentFullYear')errors.push('This residence status needs special rules before the core result can be used.');
  if(inputs['/person/deathDate'])errors.push('A deceased taxpayer needs special-return rules before the core result can be used.');
  if(inputs['/ns/claimSpouse']===true&&Number(inputs['/ns/eligibleDependantBase']??0)>0)errors.push('The Nova Scotia spouse and eligible-dependant amounts cannot both be claimed.');
  if(inputs['/schedules/useDonations']!==true&&inputs['/ns/farmerFoodDonations']!==undefined&&inputs['/ns/eligibleDonations']!==undefined&&cents(inputs['/ns/farmerFoodDonations'])>cents(inputs['/ns/eligibleDonations']))errors.push('Farmer food donations must be included in eligible donations.');
  const nsMax={'2025':11744,'2026':11932}[inputs['/return/taxYear']];
  if(nsMax&&Number(inputs['/ns/eligibleDependantBase'])>nsMax)errors.push('The Nova Scotia eligible-dependant base exceeds the annual maximum.');
  const fc=inputs['/specialTaxes/minimumTaxCarryover'],pc=inputs['/ns/federalMinimumTaxCarryover'];
  if(fc!==undefined&&pc!==undefined&&cents(fc)!==cents(pc))errors.push('The federal minimum-tax carryover must match the federal amount used in Nova Scotia tax.');
  if(inputs['/federalTax/useMinimumTaxSchedule']===false&&Number(inputs['/ns/federalAdditionalMinimumTax']??0)>0)errors.push('Nova Scotia additional minimum tax requires the federal minimum-tax schedule to be reviewed.');
  if(definitions.has('/schedule9/valid')&&(inputs['/schedules/useDonations']===true||inputs['/schedules/useRrsp']===true)){
   const candidate=build(inputs);
   if(inputs['/schedules/useDonations']===true){
    if(result(candidate,'/schedule9/valid').value==='false')errors.push('Schedule 9 claims exceed a gift pool or income limit, have an invalid origin year, or have inconsistent capital-gift amounts.');
    const gifts=result(candidate,'/schedule9/claimedGifts');if(gifts.complete&&Number(inputs['/ns/farmerFoodDonations']??0)>Number(gifts.value))errors.push('Farmer food donations must be included in the Schedule 9 gift claim.');
   }
   if(inputs['/schedules/useRrsp']===true&&result(candidate,'/schedule7/valid').value==='false')errors.push('Schedule 7 repayments, transfers or the elected deduction exceed the available contributions or room.');
  }
  return errors;
 }
 return {definitions,dictionary,build,result,validate,constraints};
}
