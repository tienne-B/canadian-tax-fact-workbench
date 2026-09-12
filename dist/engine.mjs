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
  return errors;
 }
 return {definitions,dictionary,build,result,validate,constraints};
}
