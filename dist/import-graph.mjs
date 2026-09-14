import {canonical} from './engine.mjs';
export const MAX_IMPORT_BYTES=10*1024*1024;
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const reviewPaths=new Set(['/return/annualParametersReviewed','/ns/creditsReviewed','/federalTax/returnReviewed','/schedule9/reviewed','/schedule7/reviewed']);
// Restore writable facts only. Calculated nodes are always recomputed locally.
export function prepareImport(text,engine){
 if(new TextEncoder().encode(text).length>MAX_IMPORT_BYTES)throw Error('Choose a JSON file smaller than 10 MB.');
 let data;try{data=JSON.parse(text.replace(/^\uFEFF/,''));}catch{throw Error('This file is not valid JSON.');}
 if(!object(data))throw Error('Expected a fact graph JSON object.');
 const reconciledPaths=new Set(['employmentIncome','supportIncome','deductibleSupport','athleteTrustIncome','royalties','researchGrants','supplementaryUnemployment','wageProtection','unionDues','employmentExpenses','employmentIncomeAdjustment','businessIncome','businessLosses','eligibleCapitalGains','rentalIncome','rentalLosses'].map(n=>'/nextYearRrsp/'+n));
 const reconciled=[];
 const inputs={},wrapped=data.format==='canadian-tax-graph';
 if(wrapped&&!object(data.inputs))throw Error('The graph export has no valid inputs object.');
 const source=wrapped?data.inputs:data;
 for(const [path,entry]of Object.entries(source)){
  if(!wrapped&&path==='/meta/migrationsApplied'){
   if(!object(entry)||entry.$type!=='IntWrapper'||!Number.isInteger(entry.item)||entry.item<0||entry.item>2)throw Error('This native graph uses unsupported migration metadata.');
   continue;
  }
  if(reconciledPaths.has(path)){reconciled.push(path);continue;}
  const f=engine.definitions.get(canonical(path));
  if(!f||f.formula||path.includes('*'))throw Error('Unknown or calculated input: '+path);
  let value=entry;
  if(!wrapped){
   if(!object(entry)||entry.$type!==f.type+'Wrapper')throw Error('Unexpected value type for '+path);
   value=entry.item;
   if(f.type==='Day')value=object(value)?value.date:undefined;
   if(f.type==='Collection')value=object(value)?value.items:undefined;
  }
  if(canonical(path)==='/subdivisionEDeductions/*/category'&&value==='rrsp')throw Error('This saved graph contains an RRSP deduction in Subdivision E. Move that record to Schedule 7 and remove it from Subdivision E before importing, to prevent a duplicate deduction.');
  try{engine.validate(path,value);}catch(e){throw Error(path+': '+e.message);}
  inputs[path]=value;
 }
 // Check collection membership and native engine acceptance before any UI mutation.
 engine.build(inputs);
 let clearedReviews=0;
 for(const path of Object.keys(inputs))if(path.startsWith('/review/')||reviewPaths.has(path)){
  delete inputs[path];clearedReviews++;
 }
 const graph=engine.build(inputs);
 return {inputs,graph,format:wrapped?'Nodes & edges export':'Native IRS graph',count:Object.keys(inputs).length,collections:Object.entries(inputs).filter(([p])=>engine.definitions.get(canonical(p)).type==='Collection').length,clearedReviews,warnings:[...engine.constraints(inputs),...reconciled.map(p=>p+' is now calculated from earlier answers; its old standalone value was discarded. Review the linked sources and employment adjustment.')]};
}
