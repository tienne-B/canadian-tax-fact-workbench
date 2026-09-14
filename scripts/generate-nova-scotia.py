from pathlib import Path
import json,xml.etree.ElementTree as E,hashlib,gzip
from decimal import Decimal,ROUND_HALF_UP
out=Path(__file__).resolve().parents[1]/'dist'/'nova-scotia';out.mkdir(exist_ok=True)
URL='https://nslegislature.ca/sites/default/files/legc/statutes%20HTML/income%20tax.htm'
RATE='https://www.novascotia.ca/personal-income-tax-rates-and-indexation'
CRA='https://www.canada.ca/en/revenue-agency/services/forms-publications/tax-packages-years/general-income-tax-benefit-package/nova-scotia/5003-pc.html'
def op(n,*a,**kw):return dict(op=n,args=list(a),**kw)
def dep(p):return op('Dependency',path=p if p.startswith('/') else '/ns/'+p)
def dollar(n):return op('Dollar',str(n))
def integer(n):return op('Int',str(n))
def rational(n):return op('Rational',str(n))
def sub(a,b):return op('Subtract',op('Minuend',a),op('Subtrahends',b))
def add(*a):return op('Add',*a)
def mul(a,r):return op('Multiply',a,rational(r))
def floor(a):return op('GreaterOf',dollar(0),a)
def least(a,b):return op('LesserOf',a,b)
def equal(a,b):return op('Equal',op('Left',a),op('Right',b))
def lt(a,b):return op('LessThan',op('Left',a),op('Right',b))
def case(c,v):return op('Case',op('When',c),op('Then',v))
def switch(c,v,other=None):return op('Switch',case(c,v),*([case(op('True'),other)] if other is not None else []))
facts=[];params=[]
def fact(name,typ,desc,sec,formula=None,module='nsCredits',**kw):
 f=dict(path='/ns/'+name,type=typ,module=module,kind='derived' if formula else 'reviewed_input',definition=desc,authorities=[dict(label='NS ITA',pinpoint=sec,url=URL)],formula=formula,**kw)
 if typ=='Dollar' and formula is None:f['nonnegative']=True
 facts.append(f);return dep(name)
def inp(n,desc,sec,typ='Dollar',module='nsCredits',**kw):return fact(n,typ,desc,sec,module=module,**kw)
years={2025:dict(thresholds=[30507,61015,95883,154650],basic=11744,age=5734,spouseCeiling=12618,spouseFloor=874),2026:dict(thresholds=[30995,61991,97417,157124],basic=11932,age=5826,spouseCeiling=12820,spouseFloor=888)}
rates=['879/10000','1495/10000','1667/10000','175/1000','21/100']
for y,p in years.items():
 p['baseTaxes']=[];total=Decimal(0);prev=0
 for t,r in zip(p['thresholds'],rates):
  n,d=map(Decimal,r.split('/'));total+=Decimal(t-prev)*n/d;p['baseTaxes'].append(str(total.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)));prev=t
for key in ['basic','age','spouseCeiling','spouseFloor']+['threshold'+str(i) for i in range(4)]+['baseTax'+str(i) for i in range(4)]:
 vals={y:p['thresholds'][int(key[-1])] if key.startswith('threshold') else p['baseTaxes'][int(key[-1])] if key.startswith('baseTax') else p[key] for y,p in years.items()}
 params.append(dict(path='/ns/parameters/'+key,type='Dollar',module='nsParameters',kind='derived',definition='Annual '+key+' selected by the federal tax year. No fallback for unsupported years.',authorities=[dict(label='NS ITA',pinpoint='8, 10B–10G, 22A',url=URL),dict(label='NS indexation',pinpoint='2025 / 2026',url=RATE)],formula=op('Switch',*[case(equal(dep('/return/taxYear'),integer(y)),dollar(v)) for y,v in vals.items()]),ui={'hidden':True}))
p=lambda n:dep('parameters/'+n)
fact('yearSupported','Boolean','An explicitly supplied annual parameter pack exists.','22A',op('Any',*[equal(dep('/return/taxYear'),integer(y)) for y in years]),module='nsSetup')
scope=inp('ordinaryReturnConfirmed','Confirm a living individual’s ordinary full-year Canadian resident return, resident in NS on December 31, with all income allocated to NS. No bankruptcy, separate return, trust, or multi-jurisdiction business allocation.','5, 23–29, 32',typ='Boolean',module='nsSetup')
review=inp('creditsReviewed','Confirm all provincial credit eligibility, amounts, transfers, ordering and no double counting have been reviewed for the selected year. This is an attestation, not automatic eligibility verification.','10J, 24, 25',typ='Boolean',module='nsSetup')
fact('inScope','Boolean','Provincial calculation scope and supported year. A false condition blocks tax payable instead of returning zero.','5, 23–29, 32',op('All',dep('yearSupported'),scope,equal(dep('/residence/status'),op('String','residentFullYear')),equal(dep('/residence/provinceAtYearEnd'),op('String','NS')),op('Not',op('IsComplete',dep('/person/deathDate')))),module='nsSetup')
branches=[]
for i,r in enumerate(rates):
 base=dollar(0) if i==0 else p('baseTax'+str(i-1));threshold=dollar(0) if i==0 else p('threshold'+str(i-1))
 branches.append(case(lt(dep('/taxableIncome/amount'),p('threshold'+str(i))) if i<4 else op('True'),add(base,mul(sub(dep('/taxableIncome/amount'),threshold),r))))
fact('bracketTax','Dollar','NS tax on federal taxable income, using annual thresholds and cumulative base taxes.','8, 22A',op('Switch',*branches),module='nsTax')
fact('basicPersonalBase','Dollar','Basic personal amount; no income phase-out in the supported 2025+ packs.','10B(1), 22A',p('basic'))
sp=inp('claimSpouse','Claim the eligible spouse/common-law partner amount after reviewing support, separation and federal restrictions. Cannot also claim an eligible dependant. Spouse income is read from the federal family fact.','10C, 10J',typ='Boolean')
fact('spouseBase','Dollar','Eligible spouse amount, reduced by the spouse income from the shared federal dictionary.','10C(1), 10J, 22A',switch(sp,floor(sub(p('spouseCeiling'),op('GreaterOf',p('spouseFloor'),dep('/person/spouseNetIncome')))),dollar(0)))
ed=inp('eligibleDependantBase','Reviewed eligible-dependant base under s10D, after the income reduction and restrictions. Maximum is the annual basic personal amount. Enter zero if none; exclusive of spouse claim.','10D, 10J, 22A')
ageadj=inp('ageIncomeAdjustment','Signed adjustment to federal net income for s10G: remove included s79 gains and add back the s20(1)(ww) deduction. Enter zero if neither applies.','10G',module='nsCredits');facts[-1]['nonnegative']=False
age=op('Not',lt(sub(dep('/return/taxYear'),dep('/person/birthDate/year')),integer(65)))
fact('is65OrOlder','Boolean','Age attained by December 31 from shared date of birth and taxation year.','10G, 36B',age,module='nsSetup')
fact('ageBase','Dollar','Age amount, phased out at 15% of adjusted income over $30,828. That income threshold is not indexed.','10G, 22A(4)',switch(dep('is65OrOlder'),floor(sub(p('age'),mul(floor(sub(add(dep('/income/netIncome'),ageadj),dollar(30828))),'15/100'))),dollar(0)))
pension=inp('eligiblePensionIncome','Pension income eligible under federal s118(3), before the NS $1,173 cap; zero if none.','10H')
fact('pensionBase','Dollar','Eligible pension base capped at $1,173.','10H',least(pension,dollar(1173)))
other=inp('otherNonrefundableBase','Reviewed sum of other NS base amounts before multiplying by 8.79%: caregiver, infirm dependant, young children, disability, tuition/education/carryforward, student-loan interest, CPP/EI and transfers (ss10E–10F,10I,13–19). Apply each provincial limit first. Exclude basic, spouse, eligible-dependant, age, pension, medical, naturopath and donations entered separately.','10E–10F, 10I, 13–19')
med=inp('eligibleMedicalExpenses','Reviewed eligible family medical expenses before the income threshold, as permitted by s12. Exclude amounts used by another claimant.','12')
md=inp('otherDependantMedicalBase','Reviewed total eligible medical bases for other dependants after each dependant’s income threshold and statutory limit.','12')
nat=inp('naturopathBase','Reviewed eligible naturopath expenses under s12B, including permitted dependant amounts after their limits. Exclude amounts already claimed under s12.','12B')
fact('medicalBase','Dollar','Family expenses less the lower of $1,637 and 3% of net income, floored at zero, plus reviewed dependant bases.','12',add(floor(sub(med,least(dollar(1637),mul(dep('/income/netIncome'),'3/100')))),md))
fact('ordinaryCredits','Dollar','Combined qualifying NS bases multiplied once by the lowest rate.','10B–19',mul(add(dep('basicPersonalBase'),dep('spouseBase'),ed,dep('ageBase'),dep('pensionBase'),other,dep('medicalBase'),nat),'879/10000'),module='nsTax')
gifts=inp('eligibleDonations','Qualifying gifts used for the federal s118.1 deduction and eligible under NS s11, after applicable limits.','11')
gifts=dep('/schedules/claimedGiftsForNs')
fact('donationCredit','Dollar','8.79% on the first $200 and 21% on the balance of qualifying gifts.','11',add(mul(least(gifts,dollar(200)),'879/10000'),mul(floor(sub(gifts,dollar(200))),'21/100')),module='nsTax')
a=inp('taxableEligibleDividends','Taxable eligible Canadian dividends including gross-up, already included once in federal income. Do not enter the cash dividend.','21(1)')
b=inp('taxableOtherDividends','Taxable non-eligible Canadian dividends including gross-up, already included once in federal income.','21(1A)')
fact('dividendCredit','Dollar','8.85% of taxable eligible dividends plus 1.5% of taxable other dividends (2025+).','21',add(mul(a,'885/10000'),mul(b,'15/1000')),module='nsTax')
additions=inp('federalSection9Additions','Reviewed sum of federal additions under ss120.3,120.31 and ITAR40 used by NS s9. Enter zero if none.','9',module='nsAdjustments')
tosi=inp('splitIncomeTax','Reviewed NS split-income tax under s30, after applicable adjustments. Provincial dollars, not federal TOSI.','30',module='nsAdjustments')
carry=inp('federalMinimumTaxCarryover','Federal s120.2 deduction for this year, for the provincial 57.5% carryover credit.','20',module='nsAdjustments')
amt=inp('federalAdditionalMinimumTax','Federal additional minimum tax under s120.2(3), for the provincial 57.5% addition.','31',module='nsAdjustments')
foreign=inp('foreignTaxCredit','Reviewed NS foreign tax credit after country-by-country and statutory limits. Not the federal foreign tax credit.','34',module='nsAdjustments')
fact('taxBeforeReduction','Dollar','Tax after ordinary credits, dividends, minimum-tax adjustments and provincial foreign credit, with statutory zero floors.','8–9, 20–21, 30–31, 34',floor(sub(add(floor(sub(add(dep('bracketTax'),mul(additions,'575/1000'),tosi),add(dep('ordinaryCredits'),dep('donationCredit'),dep('dividendCredit'),mul(carry,'575/1000')))),mul(amt,'575/1000')),foreign)),module='nsTax')
lir=inp('claimLowIncomeReduction','Confirm eligibility to claim s35, including age/parent/spouse tests, disqualifications, relationship rules and that a spouse has not claimed this reduction. No automatic eligibility inference.','35',typ='Boolean',module='nsReduction')
family=inp('adjustedFamilyIncome','Reviewed s35 adjusted family income: taxpayer plus qualified relation, recalculated for RDSP, UCCB, s79/s40(3.21) gains and deductions in s35(1)(a). Not simply federal net income or a benefits AFNI. Required only if claiming the reduction.','35(1)(a)',module='nsReduction')
facts[-1]['nonnegative']=False
rel=inp('qualifyingSpouseOrDependant','Confirm exactly one additional $300 amount for a qualifying relation, or qualifying eligible dependant when there is no qualifying relation. Required only if claiming reduction.','35(2)',typ='Boolean',module='nsReduction')
children=inp('otherQualifyingDependants','Number of other qualifying children/dependants for the $165 amount, excluding the dependant used for the additional $300. Required only if claiming reduction.','35(2)',typ='Int',module='nsReduction',minimum=0)
fact('lowIncomeReduction','Dollar','Reduction: $300 plus permitted $300 and $165 amounts, less 5% of adjusted family income over $15,000, floored at zero.','35',switch(lir,floor(sub(add(dollar(300),switch(rel,dollar(300),dollar(0)),op('Multiply',dollar(165),children)),mul(floor(sub(family,dollar(15000))),'5/100'))),dollar(0)),module='nsTax')
political=inp('politicalContributions','Eligible NS political contributions supported by receipts.','50',module='nsAdjustments')
food=inp('farmerFoodDonations','Fair market value of eligible farmer food donations already included in eligible donations above, after reviewing s50A qualification.','50A',module='nsAdjustments')
cert=inp('certificateCredits','Reviewed total of usable labour-sponsored, equity, innovation-equity and venture-capital credits, after their individual certificate, carryforward and annual limits. Excludes the age credit and political/food credits calculated here.','37–38',module='nsAdjustments')
fact('politicalCredit','Dollar','75% of qualifying political contributions, capped at $750 and available tax through the subsequent zero floor.','50',least(dollar(750),mul(political,'75/100')),module='nsTax')
fact('farmerFoodCredit','Dollar','25% of qualifying donated food value, claimed in addition to the charitable donation credit.','50A',mul(food,'25/100'),module='nsTax')
fact('ageTaxCredit','Dollar','$1,000 age tax credit when age 65+ and taxable income strictly below $24,000. Ordinary-return scope is required for the final result.','36B',switch(op('All',dep('is65OrOlder'),lt(dep('/taxableIncome/amount'),dollar(24000))),dollar(1000),dollar(0)),module='nsTax')
fact('taxAfterCredits','Dollar','NS income tax after the modelled nonrefundable credits and reviewed adjustments. Excludes federal tax, payments and refundable NS479 credits. This inspection fact is not gated by review.','35–38, 50–50A',floor(sub(dep('taxBeforeReduction'),add(dep('lowIncomeReduction'),dep('politicalCredit'),dep('farmerFoodCredit'),cert,dep('ageTaxCredit')))),module='nsTax')
valid=op('All',op('Not',op('All',sp,op('Not',equal(ed,dollar(0))))),op('Not',lt(p('basic'),ed)),op('Not',lt(gifts,food)))
fact('claimsConsistent','Boolean','Spouse and eligible dependant are exclusive; dependant base respects the annual maximum; food gifts are included in total eligible donations.','10C–10D, 50A',valid,module='nsSetup')
fact('taxPayable','Dollar','Reviewed NS provincial income tax for a supported ordinary return. Incomplete until scope, core review, CAD and provincial review/consistency gates are satisfied. Not total Canadian tax or balance owing.','5, 8–50A',switch(op('All',dep('inScope'),review,dep('claimsConsistent'),dep('/review/coreReady'),equal(dep('/return/currency'),op('String','CAD'))),dep('taxAfterCredits')),module='nsTax')
def xml_expr(x):
 el=E.Element(x['op'],{'path':x['path']} if 'path'in x else {})
 for a in x['args']:
  if isinstance(a,dict):el.append(xml_expr(a))
  else:el.text=a
 return el
def write_xml(fn,fs,namespaces):
 root=E.Element('FactDictionaryModule');fe=E.SubElement(root,'Facts')
 for n in namespaces:
  f=E.SubElement(fe,'Fact',path=n);E.SubElement(E.SubElement(f,'Derived'),'String').text=n
 for f in fs:
  el=E.SubElement(fe,'Fact',path=f['path']);E.SubElement(el,'Description').text=f['definition']
  expr=E.SubElement(el,'Derived' if f['formula'] else 'Writable')
  if f['formula']:expr.append(xml_expr(f['formula']))
  else:
   E.SubElement(expr,f['type'])
   if f.get('nonnegative') or 'minimum'in f:E.SubElement(E.SubElement(expr,'Limit',type='Min'),f['type']).text=str(f.get('minimum',0))
 E.indent(root);E.ElementTree(root).write(out/fn,encoding='utf-8',xml_declaration=True)
write_xml('fact-dictionary.xml',facts,['/ns']);write_xml('parameters.xml',params,['/ns/parameters'])
for fn,fs in [('catalogue.json',facts),('parameter-catalogue.json',params)]:
 (out/fn).write_text(json.dumps(dict(format='canadian-personal-income-tax-fact-catalogue',version='0.2.0-ns',scope='Ordinary full-year NS resident personal returns; 2025 and 2026 annual packs; reviewed complex entitlements.',facts=fs),indent=2)+'\n')
(out/'parameters.json').write_text(json.dumps(dict(rates=rates,years=years,notes='2026 spouse ceiling and floor rounded from 2025 under s22A. $30,828 age phase-out threshold is not indexed. No extrapolation beyond explicit packs. Base taxes accumulate exact bands, then round to cents.',sources=[URL,RATE,CRA]),indent=2)+'\n')
raw=gzip.decompress((out/'source-income-tax.html.gz').read_bytes());(out/'source-income-tax.html.gz').write_bytes(gzip.compress(raw,mtime=0))
(out/'sources.json').write_text(json.dumps(dict(retrieved='2026-09-12',act=dict(title='Income Tax Act, R.S.N.S. 1989, c. 217',url=URL,sha256=hashlib.sha256(raw).hexdigest(),snapshot='source-income-tax.html.gz',html_amended_comment='April 23, 2026; Release 80',caveat='Consolidated text is a snapshot, not a guarantee of all commencement or application provisions.'),annual_sources=[RATE,CRA,'https://novascotia.ca/just/regulations/regs/incindexation.htm']),indent=2)+'\n')
print(len(facts),'NS domain facts;',len(params),'annual parameter selectors')
