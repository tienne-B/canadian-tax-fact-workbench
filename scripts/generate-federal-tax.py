from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
import json,xml.etree.ElementTree as E
out=Path(__file__).resolve().parents[1]/'dist'/'federal-tax';out.mkdir(exist_ok=True)
URL='https://laws-lois.justice.gc.ca/eng/acts/I-3.3/FullText.html'
CRA='https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-r/5000-r-25e.txt'
def op(n,*a,**kw):return dict(op=n,args=list(a),**kw)
def d(p):return op('Dependency',path=p if p.startswith('/') else '/federalTax/'+p)
def val(n,t='Dollar'):return op(t,str(n))
def add(*a):return op('Add',*a)
def sub(a,b):return op('Subtract',op('Minuend',a),op('Subtrahends',b))
def mul(a,b):return op('Multiply',a,b)
def floor(a):return op('GreaterOf',val(0),a)
def lesser(a,b):return op('LesserOf',a,b)
def eq(a,b):return op('Equal',op('Left',a),op('Right',b))
def lt(a,b):return op('LessThan',op('Left',a),op('Right',b))
def case(a,b):return op('Case',op('When',a),op('Then',b))
def switch(a,b,c=None):return op('Switch',case(a,b),*([case(op('True'),c)] if c is not None else []))
facts=[]
def fact(n,desc,sec,formula=None,t='Dollar',module='federalCalculation',**kw):
 f=dict(path='/federalTax/'+n,type=t,module=module,kind='derived' if formula else 'reviewed_input',definition=desc,authorities=[dict(label='Federal ITA',pinpoint=sec,url=URL),dict(label='CRA T1',pinpoint=kw.pop('line','Step 5–6'),url=CRA)],formula=formula,**kw)
 if not formula and t=='Dollar':f['nonnegative']=True
 facts.append(f);return d(n)
def inp(n,desc,sec,**kw):return fact(n,desc,sec,module='federalAdjustments',**kw)
years={2025:dict(thresholds=[57375,114750,177882,253414],rates=['145/1000','205/1000','26/100','29/100','33/100'],bpaMax=16129,bpaMin=14538),2026:dict(thresholds=[58523,117045,181440,258482],rates=['14/100','205/1000','26/100','29/100','33/100'],bpaMax=16452,bpaMin=14829)}
for y,p in years.items():
 total=Decimal(0);prev=0;p['bases']=[]
 for th,r in zip(p['thresholds'],p['rates']):
  n,den=map(Decimal,r.split('/'));total+=Decimal(th-prev)*n/den;p['bases'].append(str(total.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)));prev=th
for key in ['bpaMax','bpaMin']+['threshold'+str(i) for i in range(4)]+['base'+str(i) for i in range(4)]+['rate'+str(i) for i in range(5)]:
 values={y:p['thresholds'][int(key[-1])] if key.startswith('threshold') else p['bases'][int(key[-1])] if key.startswith('base') else p['rates'][int(key[-1])] if key.startswith('rate') else p[key] for y,p in years.items()}
 typ='Rational' if key.startswith('rate') else 'Dollar'
 fact('parameters/'+key,'Annual '+key+' selected by the shared tax year. No extrapolation.','117, 117.1, 118(1.1)',op('Switch',*[case(eq(d('/return/taxYear'),val(y,'Int')),val(v,typ)) for y,v in values.items()]),t=typ,module='federalParameters',ui={'hidden':True})
p=lambda n:d('parameters/'+n)
fact('yearSupported','Explicit federal annual pack is available.','117, 117.1',op('Any',*[eq(d('/return/taxYear'),val(y,'Int')) for y in years]),t='Boolean')
scope=inp('ordinaryReturnConfirmed','Confirm a living individual’s ordinary full-year Canadian resident return, all income allocated to Nova Scotia, no separate return, bankruptcy, trust or foreign provincial allocation. Special schedules are entered as reviewed amounts.','2, 114, 120',t='Boolean')
review=inp('returnReviewed','Confirm federal credit-dollar amounts, special schedules, income adjustments, provincial tax, payments and refundable credits are complete and reviewed. Zero means confirmed none, not unknown.','118–127.55, 152, 164',t='Boolean')
fact('ready','Shared core, federal review and ordinary scope are satisfied.','2, 117–127.55',op('All',scope,review,d('yearSupported'),d('/review/coreReady'),eq(d('/return/currency'),val('CAD','String')),eq(d('/residence/status'),val('residentFullYear','String')),eq(d('/residence/provinceAtYearEnd'),val('NS','String')),op('Not',op('IsComplete',d('/person/deathDate')))),t='Boolean')
branches=[]
for i in range(5):branches.append(case(lt(d('/taxableIncome/amount'),p('threshold'+str(i))) if i<4 else op('True'),add(val(0) if i==0 else p('base'+str(i-1)),mul(sub(d('/taxableIncome/amount'),val(0) if i==0 else p('threshold'+str(i-1))),p('rate'+str(i))))))
fact('taxOnTaxableIncome','Progressive federal tax on shared taxable income. The lowest annual rate is 14.5% in 2025 and 14% in 2026.','117(2)',op('Switch',*branches),line='Step 5 Part A')
adj=inp('basicPersonalIncomeAdjustment','Signed adjustment to net income for the basic-personal phase-out under s118(1.1): exclude applicable s79/s40(3.21) gains and add back s20(1)(ww). Enter zero if none.','118(1.1)');facts[-1]['nonnegative']=False
reduction=op('Divide',op('Dividend',mul(sub(p('bpaMax'),p('bpaMin')),lesser(floor(sub(add(d('/income/netIncome'),adj),p('threshold2'))),sub(p('threshold3'),p('threshold2'))))),op('Divisors',sub(p('threshold3'),p('threshold2'))))
fact('basicPersonalBase','Basic personal amount reduced linearly from the maximum to the minimum across the fourth income bracket.','118(1.1)',sub(p('bpaMax'),reduction),line='30000')
# Ordinary claim amounts and existing credit-dollar exports have explicit units.
basis=fact('creditInputBasis','Choose Claim amounts for ordinary federal amounts before the credit rate, or Credit dollars for already-calculated reductions from an older export. Donations and top-up are always final credit dollars.','118–118.9',t='String',module='credits',values=['claimAmounts','creditDollars'])
claimMode=eq(basis,val('claimAmounts','String'))
def halfUpCredit(amount,n,den):
 cents=op('RoundToInt',mul(amount,val('100/1','Rational')))
 remainder=op('Modulo',mul(op('Modulo',cents,val(2*den,'Int')),val(n,'Int')),val(2*den,'Int'))
 raw=mul(amount,d('nonrefundableCreditRate'))
 corrected=add(raw,switch(eq(remainder,val(den//2,'Int')),val('0.01'),val(0)))
 return switch(lt(amount,val('21474836.48')),corrected,raw)
def atCreditRate(amount):
 return op('Switch',case(eq(d('/return/taxYear'),val(2025,'Int')),halfUpCredit(amount,145,1000)),case(eq(d('/return/taxYear'),val(2026,'Int')),halfUpCredit(amount,14,100)))
fact('nonrefundableCreditRate','Federal nonrefundable credit rate: 14.5% for 2025, 14% for 2026. Donations and top-up are added after this rate.','118(1)',p('rate0'),t='Rational',line='Step 5 Part B line 114')
selectedBase=switch(op('IsComplete',d('/credits/basicPersonal')),d('/credits/basicPersonal'),d('basicPersonalBase'))
fact('basicPersonalCredit','Basic personal credit. Optional override follows Credit input basis: base amount in Claim amounts mode; final reduction in Credit dollars mode. Blank uses the automatic income-dependent base.','118(1),118(1.1)',switch(claimMode,atCreditRate(selectedBase),switch(op('IsComplete',d('/credits/basicPersonal')),d('/credits/basicPersonal'),atCreditRate(d('basicPersonalBase')))))
extra=inp('otherNonrefundableCredits','Other ordinary federal claims absent from named fields, after eligibility limits. Enter claim bases in Claim amounts mode or final reductions in Credit dollars mode. Exclude donations, top-up and every separately entered amount.','118–118.9',line='35000')
creditnames=['spouseOrPartner','eligibleDependant','caregiver','age','pension','employment','medical','disability','tuition','tuitionCarryforward','studentLoanInterest','cppEiQpip','spousalTransfer','tuitionTransfer']
fact('ordinaryClaimAmounts','Total ordinary claim bases, including the selected basic personal amount. Available only in Claim amounts mode. Donations and top-up excluded.','118–118.9',switch(claimMode,add(selectedBase,*[d('/credits/'+n) for n in creditnames],extra)),line='33500')
legacy=add(d('basicPersonalCredit'),*[d('/credits/'+n) for n in creditnames],extra)
ordinary=op('Switch',case(claimMode,atCreditRate(d('ordinaryClaimAmounts'))),case(eq(basis,val('creditDollars','String')),legacy))
fact('ordinaryNonrefundableCredit','Ordinary claim amounts multiplied once by the annual credit rate, rounded once. Credit dollars mode instead sums already-calculated reductions.','118–118.9',ordinary,line='33800')
fact('nonrefundableCredits','Ordinary nonrefundable credit plus donations and top-up credit dollars. Neither donations nor top-up is multiplied by the ordinary rate.','118–118.9',add(d('ordinaryNonrefundableCredit'),d('/schedules/federalDonationCredit'),d('/credits/topUp')),line='35000')
fact('basicFederalTax','Federal bracket tax plus TOSI, less nonrefundable credits, dividend credit and minimum-tax carryover, floored at zero.','117–121,120.2,120.4',floor(sub(add(d('taxOnTaxableIncome'),d('/specialTaxes/splitIncome')),add(d('nonrefundableCredits'),d('/credits/dividend'),d('/specialTaxes/minimumTaxCarryover')))),line='42900')
recapture=inp('investmentCreditRecapture','Investment tax credit recapture from Form T2038(IND).','127',line='Step 5 Part C')
logging=inp('loggingTaxCredit','Permitted federal logging tax credit after limits.','127(1)',line='Step 5 Part C')
fact('federalTaxAfterForeignCredit','Basic federal tax less the permitted foreign credit, plus investment credit recapture, less logging credit, floored at zero. Foreign surtax is outside the ordinary NS allocation scope.','126–127',floor(sub(add(sub(d('basicFederalTax'),d('/credits/foreign')),recapture),logging)),line='40600')
itc=inp('investmentTaxCredit','Permitted nonrefundable investment tax credit after limits and recapture review. Refundable ITC belongs in payments.','127',line='41200')
labour=inp('labourSponsoredCredit','Permitted federal labour-sponsored funds credit after applicable limits.','127.4',line='41400')
fact('regularTaxAfterCredits','Federal tax after political, investment and labour-sponsored credits, floored at zero.','127,127.4',floor(sub(d('federalTaxAfterForeignCredit'),add(d('/credits/political'),itc,labour))),line='41700 before T691 replacement')
amt=inp('useMinimumTaxSchedule','Has T691 determined the amount to report on line 41700? If yes, enter the FINAL line 41700 amount from T691 in Minimum tax in Other tax & filing. This replaces regular tax; it is not an added AMT amount.','127.5–127.55',t='Boolean',line='41700')
fact('taxAfterCredits','Line 41700: regular calculation, or the reviewed final T691 result when the minimum-tax schedule applies.','127.5–127.55',switch(amt,d('/specialTaxes/minimumTax'),d('regularTaxAfterCredits')),line='41700')
acwb=inp('advancedWorkersBenefit','Advanced Canada workers benefit amount required on line 41500 from Schedule 6. Enter the CWB credit separately among refundable credits.','122.72',line='41500')
special=inp('specialTaxes41800','Reviewed total special taxes included on T1 line 41800. Exclude TOSI, AMT, OAS/EI repayments and taxes reported on separate returns (including separate registered-plan tax forms).','120.3,120.31 and applicable charging provisions',line='41800')
fact('netFederalTaxBeforeReview','Line 41700 plus ACWB and line 41800 special taxes. Inspection amount; final output is review gated.','117–127.55',add(d('taxAfterCredits'),acwb,special),line='42000')
fact('netFederalTax','Reviewed net federal tax; does not include provincial tax or contributions and repayments on Step 6.','117–127.55',switch(d('ready'),d('netFederalTaxBeforeReview')),line='42000')
cpp=inp('cppContributionsPayable','CPP payable on self-employment and other earnings from Schedule 8/RC381. Separate from the deductible and creditable CPP portions already included in income/credits.','CPP Act; T1 Step 6',line='42100')
ei=inp('eiPremiumsPayable','EI premiums payable on self-employment and other eligible earnings from Schedule 13.','EI Act; T1 Step 6',line='42120')
eiRecovery=inp('eiBenefitsRepayment','EI benefits repayment included in line 23500/42200. Exclude the OAS recovery tax supplied in Other tax & filing. Review the corresponding income deduction separately.','EI Act; 60(v.1)',line='42200')
fact('socialBenefitsRepayment','OAS recovery tax plus EI benefits repayment. Review any corresponding net-income deduction; do not deduct the payable twice.','180.2; EI Act',add(d('/specialTaxes/oasRecovery'),eiRecovery),line='42200')
fact('provincialTax','Reviewed NS tax read by reference from the separate provincial module.','NS ITA; T1 Step 6',d('/ns/taxPayable'),line='42800')
fact('provincialSchedulesConsistent','Shared minimum-tax carryover agrees with the amount entered for NS, and no NS additional minimum tax is claimed when T691 is not used. Other special-schedule correspondence remains subject to review.','120.2,127.5; NS ITA20,31',op('All',eq(d('/specialTaxes/minimumTaxCarryover'),d('/ns/federalMinimumTaxCarryover')),op('Any',d('useMinimumTaxSchedule'),eq(d('/ns/federalAdditionalMinimumTax'),val(0)))),t='Boolean')
fact('totalPayable','Combined federal and provincial tax plus CPP/EI payable and social benefits repayment, before payments and refundable credits.','T1 Step 6',switch(d('provincialSchedulesConsistent'),add(d('netFederalTax'),d('provincialTax'),cpp,ei,d('socialBenefitsRepayment'))),line='43500',module='settlement')
refunds=[('cppQppOverpayment','44800','CPP/QPP overpayment from Schedule 8 or RC381'),('eiOverpayment','45000','EI overpayment'),('refundableMedicalSupplement','45200','Refundable medical expense supplement'),('workersBenefit','45300','Canada workers benefit from Schedule 6; ACWB goes separately on line 41500'),('canadaTrainingCredit','45350','Canada training credit from Schedule 11'),('multigenerationalRenovationCredit','45355','Multigenerational home renovation credit from Schedule 12'),('investmentCreditRefund','45400','Refundable investment tax credit'),('partXII2Credit','45600','Part XII.2 credit from applicable slips'),('gstHstRebate','45700','Employee/partner GST/HST rebate from GST370; not GST/HST benefit payments'),('educatorSupplyCredit','46900','Eligible educator school supply CREDIT DOLLARS after the 25% rate and $1,000 expense limit'),('journalismLabourCredit','47555','Canadian journalism labour tax credit'),('fuelChargeFarmerCredit','47556','Return of fuel-charge proceeds to farmers credit'),('provincialRefundableCredits','47900','Reviewed NS479 refundable credits; separate from NS428 nonrefundable credits')]
for n,line,desc in refunds:fact(n,desc+'. Enter zero only after confirming none applies.','T1 Step 6; applicable refundable-credit provision',line=line,module='refundableCredits')
fact('refundableCredits','Sum of reviewed refundable-credit and overpayment amounts, excluding withholding and instalments. Quebec abatement is not applicable to this NS scope.','T1 Step 6',add(*[d(n) for n,_,_ in refunds]),module='settlement')
fact('totalCreditsAndPayments','Tax withheld, instalments, refundable credits and overpayments. Do not include benefits paid outside the T1 reconciliation.','153,156,164; T1 Step 6',add(d('/payments/taxWithheld'),d('/payments/instalments'),d('refundableCredits')),line='48200',module='settlement')
fact('netPayable','Signed reconciliation: total payable minus credits/payments. Positive means owing; negative means a calculated refund.','156.1,164',sub(d('totalPayable'),d('totalCreditsAndPayments')),line='43500 minus 48200',module='settlement')
fact('amountOwing','Calculated balance owing, floored at zero. Excludes arrears, interest, penalties, CRA account offsets and assessment changes.','156.1',floor(d('netPayable')),line='48500',module='settlement')
fact('refund','Calculated refund magnitude, floored at zero; not a refund already assessed or issued by CRA.','164',floor(sub(val(0),d('netPayable'))),line='48400',module='settlement')
def xml(x):
 e=E.Element(x['op'],{'path':x['path']} if 'path'in x else {})
 for a in x.get('args',[]):
  if isinstance(a,dict):e.append(xml(a))
  else:e.text=str(a)
 return e
root=E.Element('FactDictionaryModule');ff=E.SubElement(root,'Facts')
for ns in ['/federalTax','/federalTax/parameters']:
 f=E.SubElement(ff,'Fact',path=ns);E.SubElement(E.SubElement(f,'Derived'),'String').text=ns
for f in facts:
 el=E.SubElement(ff,'Fact',path=f['path']);E.SubElement(el,'Description').text=f['definition'];ex=E.SubElement(el,'Derived' if f['formula'] else 'Writable')
 if f['formula']:ex.append(xml(f['formula']))
 else:
  E.SubElement(ex,f['type'])
  if f.get('nonnegative'):E.SubElement(E.SubElement(ex,'Limit',type='Min'),'Dollar').text='0'
E.indent(root);E.ElementTree(root).write(out/'fact-dictionary.xml',encoding='utf-8',xml_declaration=True)
(out/'catalogue.json').write_text(json.dumps(dict(version='0.3.1',facts=facts),indent=2)+'\n')
(out/'parameters.json').write_text(json.dumps(dict(years=years,sources=[CRA,'https://www.canada.ca/en/revenue-agency/services/tax/individuals/tax-rates-brackets.html','https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4032-payroll-deductions-tables/t4032oc-jan/t4032oc-january-general-information.html'],retrieved='2026-09-12',notes='2026 final-return layout not yet verified. Formula sequence follows 2025 T1. Base taxes use exact bands before rounding.'),indent=2)+'\n')
print(len(facts),'federal tax and settlement facts')
