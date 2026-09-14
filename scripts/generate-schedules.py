from pathlib import Path
import json,xml.etree.ElementTree as E,gzip,hashlib
out=Path(__file__).resolve().parents[1]/'dist'/'schedules';out.mkdir(exist_ok=True)
S9='https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s9/5000-s9-25e.txt'
S7='https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s7/5000-s7-25e.txt'
GUIDE='https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4040/rrsps-other-registered-plans-retirement.html'
def op(n,*a,**kw):return dict(op=n,args=list(a),**kw)
def d(p):return op('Dependency',path=p)
def v(n,t='Dollar'):return op(t,str(n))
def add(*a):return op('Add',*a)
def sub(a,b):return op('Subtract',op('Minuend',a),op('Subtrahends',b))
def mul(a,r):return op('Multiply',a,v(r,'Rational'))
def lo(a):return op('GreaterOf',v(0),a)
def minimum(a,b):return op('LesserOf',a,b)
def compare(n,a,b):return op(n,op('Left',a),op('Right',b))
def eq(a,b):return compare('Equal',a,b)
def le(a,b):return op('Not',compare('LessThan',b,a))
def case(a,b):return op('Case',op('When',a),op('Then',b))
def switch(a,b,c=None):return op('Switch',case(a,b),*([case(op('True'),c)] if c is not None else []))
def active(path):return switch(op('IsComplete',d(path)),d(path),op('False'))
def total(path):return op('CollectionSum',d(path))
facts=[]
def f(path,desc,expr=None,t='Dollar',module=None,line='',**kw):
 module=module or ('donations' if path.startswith(('/schedule9','/donationGifts','/donatedDepreciable')) else 'rrspRoom' if path.startswith('/rrspRoom') else 'rrspSchedule')
 src=S9 if module=='donations' else GUIDE if module in ('rrspRoom','nextYearRrsp','employments','businesses','properties') else S7
 x=dict(path=path,type=t,module=module,kind='derived' if expr else 'reviewed_input',definition=desc,formula=expr,authorities=[dict(label='CRA '+('Schedule 9' if src==S9 else 'T4040' if src==GUIDE else 'Schedule 7'),pinpoint=line,url=src)],**kw)
 if not expr and t=='Dollar':x.setdefault('nonnegative',True)
 facts.append(x);return d(path)
def inp(p,desc,**kw):return f(p,desc,**kw)
year=d('/return/taxYear')
supported=op('Any',eq(year,v(2025,'Int')),eq(year,v(2026,'Int')))
f('/schedules/yearSupported','Schedule packs exist for the selected tax year.',supported,t='Boolean',module='scheduleSetup')
for path,desc in [('/schedules/useDonations','Use Schedule 9 to supply both federal donations credit and the eligible gift claim for Nova Scotia. Manual donation-credit fields are ignored while enabled.'),('/schedules/useRrsp','Use Schedule 7 to add RRSP deductions and HBP/LLP shortfall income to shared income automatically. Remove those amounts from generic income/deduction records first.')]:f(path,desc,t='Boolean',module='scheduleSetup')
# Schedule 9 ledger: claim elections rather than an automatic optimization.
f('/donationGifts','Gift pools per origin year and category. Use remaining eligible receipt/certificate amounts after prior claims, advantages and spouse allocation. Confirm an empty collection when none.',t='Collection')
for key,desc,t in [('source','Receipt, certificate or pool reference; spouse ownership/allocation evidence.','String'),('giftYear','Origin tax year, including carryforward gifts.','Int'),('category','Ordinary categories follow lines 1–4; cultural and ecological gifts follow line 11.','String'),('available','Eligible unclaimed amount available before this return. Exclude gifts already used on the 2024 return, including the Jan–Feb 2025 extension.','Dollar'),('claim','Amount elected for this return. Use older eligible gifts first within their applicable class; do not claim the same gift for both spouses.','Dollar')]:
 kw={'values':['charity','government','foreignUniversity','unOrRegisteredForeignCharity','cultural','ecological']} if key=='category' else {}
 f('/donationGifts/*/'+key,desc,t=t,**kw)
g=lambda k:d('/donationGifts/*/'+k)
ordinary=op('Any',*[eq(g('category'),v(k,'String')) for k in ['charity','government','foreignUniversity','unOrRegisteredForeignCharity']])
eco=eq(g('category'),v('ecological','String'))
expiry=add(g('giftYear'),switch(eco,v(10,'Int'),v(5,'Int')))
f('/donationGifts/*/expiryYear','Last year to claim this pool (five years; ten for ecological gifts in the supported carryforward window).',expiry,t='Int')
window=op('All',le(g('giftYear'),year),le(year,g('expiryYear')))
valid=op('All',le(g('giftYear'),year),le(g('claim'),g('available')),op('Any',eq(g('claim'),v(0)),window))
f('/donationGifts/*/invalidClaim','Counts claims above the pool or outside its permitted origin-year window.',switch(valid,v(0),v(1)))
f('/donationGifts/*/ordinaryClaim','Claim elected within the ordinary category.',switch(ordinary,g('claim'),v(0)))
f('/donationGifts/*/specialClaim','Ecological/cultural claim elected outside the ordinary income limit.',switch(ordinary,v(0),g('claim')))
f('/donationGifts/*/oldEcologicalClaim','Ecological gifts from 2015 still eligible in 2025 are excluded from the 33% rate.',switch(op('All',eco,compare('LessThan',g('giftYear'),v(2016,'Int'))),g('claim'),v(0)))
remaining=lo(sub(g('available'),g('claim')))
f('/donationGifts/*/carryforward','Unclaimed eligible amount with at least one future year remaining.',switch(compare('LessThan',year,g('expiryYear')),remaining,v(0)))
f('/donationGifts/*/expiredUnclaimed','Unclaimed amount expiring this year or already expired.',switch(le(g('expiryYear'),year),remaining,v(0)))
f('/donatedDepreciable','One chart per depreciable-property class. Aggregate min(net proceeds, capital cost) across gifts in that class before entering the class result.',t='Collection')
f('/donatedDepreciable/*/classReference','CCA class and supporting gift calculation.',t='String')
f('/donatedDepreciable/*/recapture','Gift-related recapture included in this return, limited to the gift portion after advantages.')
f('/donatedDepreciable/*/eligiblePropertyTotal','Sum, for this class, of min(net proceeds, capital cost) for each donated property.')
f('/donatedDepreciable/*/boost','Schedule 9 line 33700 class amount.',minimum(d('/donatedDepreciable/*/recapture'),d('/donatedDepreciable/*/eligiblePropertyTotal')))
cap=inp('/schedule9/giftTaxableCapitalGains','Current-year taxable capital gains attributable to donated property, after gift-portion adjustments. Already included once in the capital-income facts.',line='33900 chart line 1')
capded=inp('/schedule9/giftCapitalGainsDeduction','Capital gains deduction attributable to those donated-property gains. Already claimed in Division C where applicable.',line='33900 chart line 2')
review=inp('/schedule9/reviewed','Confirm qualified donees, certificates, receipt eligibility, carryforward ages/oldest-first ordering, spouse allocation and capital-property charts. US treaty-limited gifts, estates and special-return rules require external review outside this ordinary schedule.',t='Boolean')
f('/schedule9/depreciableBoost','Total line 33700 from class charts.',total('/donatedDepreciable/*/boost'))
f('/schedule9/capitalBoost','Line 33900: taxable gains less related capital gains deduction.',lo(sub(cap,capded)))
f('/schedule9/ordinaryLimit','Lesser of net income and 75% of net income plus 25% of eligible capital-property amounts.',minimum(d('/income/netIncome'),add(mul(d('/income/netIncome'),'75/100'),mul(add(d('/schedule9/depreciableBoost'),d('/schedule9/capitalBoost')),'25/100'))),line='9')
for name,target in [('ordinaryClaim','ordinaryClaim'),('specialClaim','specialClaim'),('oldEcologicalClaim','oldEcologicalClaim'),('carryforward','carryforward'),('expiredUnclaimed','expiredUnclaimed')]:f('/schedule9/'+name,'Total '+name+' across the elected gift pools.',total('/donationGifts/*/'+target))
f('/schedule9/valid','Claims fit available pools, origin years and the ordinary-income limit; capital deduction does not exceed related gains.',op('All',eq(total('/donationGifts/*/invalidClaim'),v(0)),le(d('/schedule9/ordinaryClaim'),d('/schedule9/ordinaryLimit')),le(capded,cap)),t='Boolean')
f('/schedule9/claimedGifts','Total eligible elected gifts; fed and NS share this exact claim. Incomplete until validated and reviewed.',switch(op('All',supported,review,d('/schedule9/valid')),add(d('/schedule9/ordinaryClaim'),d('/schedule9/specialClaim'))),line='12')
f('/schedule9/first200','First $200 of the total eligible claim.',minimum(v(200),d('/schedule9/claimedGifts')))
f('/schedule9/above200','Eligible claim exceeding the first $200.',lo(sub(d('/schedule9/claimedGifts'),d('/schedule9/first200'))))
f('/schedule9/at33Percent','Lesser of donations above $200 excluding old ecological gifts and taxable income over the top-bracket threshold.',minimum(lo(sub(d('/schedule9/above200'),d('/schedule9/oldEcologicalClaim'))),lo(sub(d('/taxableIncome/amount'),d('/federalTax/parameters/threshold3')))),line='20')
f('/schedule9/at29Percent','Remaining claim above $200.',sub(d('/schedule9/above200'),d('/schedule9/at33Percent')),line='21')
f('/schedule9/federalCredit','First $200 at the annual lowest federal rate, plus 33% and 29% portions. This final credit is outside the ordinary nonrefundable-credit percentage.',add(op('Multiply',d('/schedule9/first200'),d('/federalTax/nonrefundableCreditRate')),mul(d('/schedule9/at33Percent'),'33/100'),mul(d('/schedule9/at29Percent'),'29/100')),line='34900')
f('/schedule9/novaScotiaCredit','8.79% of first $200 plus 21% of the balance of the same elected eligible gifts.',add(mul(d('/schedule9/first200'),'879/10000'),mul(d('/schedule9/above200'),'21/100')))
# Chart 3: prior-year inputs, deliberately not current taxable/net income.
for n,desc,typ,kw in [('openingRoomProvided','Provide signed opening unused deduction room directly (CRA statement/Chart 3 footnote 3). No means calculate it from prior limit and deductions.','Boolean',{}),('openingUnusedRoom','Signed prior-year unused deduction room, including a negative balance where applicable.','Dollar',{'nonnegative':False}),('priorDeductionLimit','Prior-year RRSP deduction limit.','Dollar',{}),('priorOrdinaryDeduction','Prior-year deduction excluding eligible transfers and specified PSPA recontributions.','Dollar',{}),('priorEmployerPrpp','Prior-year employer PRPP contributions.','Dollar',{})]:f('/rrspRoom/'+n,desc,t=typ,**kw)
f('/rrspRoom/openingRoom','Chart 3 step 1 signed unused room; direct statement value or prior limit less prior ordinary deduction and employer PRPP.',switch(d('/rrspRoom/openingRoomProvided'),d('/rrspRoom/openingUnusedRoom'),sub(d('/rrspRoom/priorDeductionLimit'),add(d('/rrspRoom/priorOrdinaryDeduction'),d('/rrspRoom/priorEmployerPrpp')))))
prior={
'employmentIncome':'Prior-year employment earnings (10100 + 10400).',
'royalties':'Author/inventor royalties included in employment income above.',
'researchGrants':'Net research grants included in employment income above.',
'supplementaryUnemployment':'Supplementary unemployment payments included above.',
'wageProtection':'Wage Earner Protection payments included above.',
'unionDues':'Dues attributable to the employment earnings above.',
'employmentExpenses':'Employment expenses attributable to those earnings.',
'businessIncome':'Positive active business income, excluding amateur-athlete trust distributions; losses entered separately.',
'postdoctoralIncome':'Postdoctoral fellowship income not already in business income.',
'disabilityPension':'CPP/QPP disability benefits (not regular retirement pensions).',
'rentalIncome':'Positive net rent from real property (not dividends, interest or capital gains).',
'supportIncome':'Taxable support and qualifying previously deducted support repaid to you.',
'athleteTrustIncome':'Qualifying performance income contributed to an amateur athlete trust.',
'businessLosses':'Active-business losses as a positive amount.',
'eligibleCapitalGains':'Taxable eligible-capital-property gains included in the business amount, where applicable.',
'rentalLosses':'Real-property rental losses as a positive amount.',
'deductibleSupport':'Deductible support and qualifying repaid support deducted for the prior year.'}
for n,desc in prior.items():f('/rrspRoom/'+n,'T4040 Chart 3 prior tax year: '+desc,line='Step 2')
r=lambda n:d('/rrspRoom/'+n)
excluded=add(*[r(n) for n in ['royalties','researchGrants','supplementaryUnemployment','wageProtection']])
f('/rrspRoom/adjustedEmployment','Chart 3 line 15: employment less separately handled inclusions, dues and expenses, floored at zero.',lo(sub(r('employmentIncome'),add(excluded,r('unionDues'),r('employmentExpenses')))))
f('/rrspRoom/earnedIncome','Chart 3 earned income: adjusted employment plus permitted inclusions less business/rental losses and deductible support. Can be negative; excludes ordinary investment income.',sub(add(r('adjustedEmployment'),excluded,*[r(n) for n in ['businessIncome','postdoctoralIncome','disabilityPension','rentalIncome','supportIncome','athleteTrustIncome']]),add(*[r(n) for n in ['businessLosses','eligibleCapitalGains','rentalLosses','deductibleSupport']])),line='29')
f('/rrspRoom/annualDollarLimit','Annual new-room ceiling, not personal total room.',op('Switch',case(eq(year,v(2025,'Int')),v(32490)),case(eq(year,v(2026,'Int')),v(33810))),line='31')
for n,desc in [('pensionAdjustment','Prior-year PA plus applicable connected-person and foreign-plan prescribed adjustments.'),('pensionAdjustmentReversal','Current-year PAR/PAC from T10.'),('exemptPspa','Prior-year exempt PSPA/PCC from T215.'),('certifiedPspa','Current-year certified PSPA from T1004.'),('qualifyingWithdrawals','Current-year qualifying withdrawals designated on T1006; may make net PSPA negative.')]:f('/rrspRoom/'+n,desc)
f('/rrspRoom/newRoom','Lesser of 18% of prior earned income and annual dollar limit, less PA, floored at zero.',lo(sub(minimum(mul(r('earnedIncome'),'18/100'),r('annualDollarLimit')),r('pensionAdjustment'))))
f('/rrspRoom/netPspa','Exempt plus certified PSPA less qualifying withdrawals; may be negative.',sub(add(r('exemptPspa'),r('certifiedPspa')),r('qualifyingWithdrawals')))
f('/rrspRoom/unflooredLimit','Signed pre-floor room: opening + new room + PAR - net PSPA.',sub(add(r('openingRoom'),r('newRoom'),r('pensionAdjustmentReversal')),r('netPspa')))
f('/rrspRoom/estimatedDeductionLimit','Chart 3 estimated current-year deduction limit, floored at zero. Compare with latest CRA assessment before relying on it.',lo(r('unflooredLimit')),line='46')
# Schedule 7, Parts A-F.
s=lambda n:d('/schedule7/'+n)
f('/schedule7/limitSource','Select the latest CRA deduction limit in Plans & loss balances, or the T4040 estimate after reviewing its inputs.',t='String',values=['craAssessment','t4040Estimate'])
f('/schedule7/deductionLimit','Selected deduction limit; the estimate must be for the shared return year.',op('Switch',case(eq(s('limitSource'),v('craAssessment','String')),d('/registeredPlans/rrspDeductionLimit')),case(eq(s('limitSource'),v('t4040Estimate','String')),r('estimatedDeductionLimit'))))
items={
'openingUnusedContributions':'Previously reported contributions available to deduct (not unused deduction room). Includes applicable current-year first-60-day receipts already reported on the previous return.',
'ownMainPeriod':'Eligible own RRSP/PRPP/SPP contributions in the main reporting period: Mar 4–Dec 31, 2025; Mar 3–Dec 31, 2026. Include eligible transfers/repayments, exclude employer PRPP and excluded/refunded contributions.',
'spousalMainPeriod':'Eligible spouse/common-law RRSP/SPP contributions in the same main reporting period, using your deduction room.',
'ownFollowing60Days':'Eligible own contributions Jan 1–Mar 2, 2026 (2025 return) or Jan 1–Mar 1, 2027 (2026 return). These are reported even if reserved for a later deduction year.',
'spousalFollowing60Days':'Eligible spouse/common-law RRSP/SPP contributions in the corresponding following-year first-60-day reporting period.',
'openingOwnRepaymentEligible':'Portion of opening unused contributions made to your own plan in the current calendar year and eligible for HBP/LLP repayment. Must be included in opening unused; not previously deducted/designated/refunded.',
'hbpRepayment':'Eligible contributions designated to repay HBP. Own plans only, not deductible.',
'llpRepayment':'Eligible contributions designated to repay LLP. Own plans only, not deductible.',
'hbpRequired':'CRA minimum required HBP repayment for this year. Enter zero for deferred repayment years; do not infer it simply from outstanding balance.',
'llpRequired':'CRA minimum required LLP repayment for this year.',
'employerPrpp':'Employer PRPP contributions reported at 20810; excluded from personal contribution receipts and reduces personal deductible room.',
'eligibleTransfers':'Eligible Schedule 7 line 15 transfers included in own contributions and taxable source income. Exclude direct tax-deferred transfers not reportable on Schedule 7. Does not consume ordinary deduction room.',
'ordinaryDeductionChosen':'Ordinary contributions elected to deduct this year, excluding transfers. May be less than the maximum to carry contributions forward.',
'hbpWithdrawals':'Qualifying HBP withdrawals from T4RSP box 27 for Part E; not ordinary taxable RRSP withdrawals.',
'llpWithdrawals':'Qualifying LLP withdrawals from T4RSP box 25 for Part E.',
'athleteTrustContributions':'Qualifying current-year amateur-athlete trust contributions for Part F. Relevant to next-year earned income, not the current-year prior-income room calculation.'}
for n,desc in items.items():f('/schedule7/'+n,desc)
f('/schedule7/hbpHomeAddressMatches','Part E: HBP purchased-home address matches the return.',t='Boolean')
f('/schedule7/llpSpouseStudent','Part E: designate spouse/common-law partner as LLP student in the first withdrawal year.',t='Boolean')
f('/schedule7/reviewed','Confirm receipt periods, transfer eligibility, age/annuitant restrictions, repayment minima and exclusions; ensure RRSP deductions and repayment-shortfall income are removed from generic records before enabling automatic posting.',t='Boolean')
f('/schedule7/newContributions','Schedule 7 line 4, personal and spousal receipts in both reporting periods.',add(*[s(n) for n in ['ownMainPeriod','spousalMainPeriod','ownFollowing60Days','spousalFollowing60Days']]),line='24500')
f('/schedule7/totalContributions','Opening unused plus new reported contributions.',add(s('openingUnusedContributions'),s('newContributions')),line='5')
f('/schedule7/repayments','HBP plus LLP designations, excluded from deductions.',add(s('hbpRepayment'),s('llpRepayment')),line='9')
f('/schedule7/availableToDeduct','Total contributions less designations.',sub(s('totalContributions'),s('repayments')),line='10')
f('/schedule7/personalDeductionRoom','Deduction limit less employer PRPP, floored at zero.',lo(sub(s('deductionLimit'),s('employerPrpp'))),line='13')
f('/schedule7/maxOrdinaryDeduction','Lesser of personal room and contributions available excluding transfers.',lo(minimum(s('personalDeductionRoom'),sub(s('availableToDeduct'),s('eligibleTransfers')))),line='17')
f('/schedule7/valid','Contribution/repayment/transfer subsets and elected deduction are consistent. A claim exceeding the maximum blocks posting instead of silently truncating it.',op('All',le(s('openingOwnRepaymentEligible'),s('openingUnusedContributions')),le(s('repayments'),add(s('ownMainPeriod'),s('ownFollowing60Days'),s('openingOwnRepaymentEligible'))),le(s('repayments'),s('totalContributions')),le(add(s('repayments'),s('eligibleTransfers')),add(s('ownMainPeriod'),s('ownFollowing60Days'),s('openingOwnRepaymentEligible'))),le(s('eligibleTransfers'),add(s('ownMainPeriod'),s('ownFollowing60Days'))),le(s('eligibleTransfers'),s('availableToDeduct')),le(s('ordinaryDeductionChosen'),s('maxOrdinaryDeduction'))),t='Boolean')
f('/schedule7/deduction','Schedule 7 line 20: eligible transfers plus elected ordinary deduction, bounded by available contributions.',switch(op('All',supported,s('reviewed'),s('valid')),minimum(s('availableToDeduct'),add(s('eligibleTransfers'),s('ordinaryDeductionChosen')))),line='20800')
f('/schedule7/unusedContributionsCarryforward','Undeducted contributions remaining after this return; distinct from unused deduction room.',sub(s('availableToDeduct'),s('deduction')),line='23')
f('/schedule7/hbpShortfall','Required HBP repayment less designation, floored at zero.',lo(sub(s('hbpRequired'),s('hbpRepayment'))),line='12900')
f('/schedule7/llpShortfall','Required LLP repayment less designation, floored at zero.',lo(sub(s('llpRequired'),s('llpRepayment'))),line='12900')
f('/schedule7/shortfallIncome','Taxable HBP/LLP shortfalls. Qualifying Part E withdrawals are not added as income.',switch(op('All',supported,s('reviewed'),s('valid')),add(s('hbpShortfall'),s('llpShortfall'))))
f('/rrspRoom/contributionSpaceBeforeNewDeposits','Selected current-year deduction limit less opening undeducted contributions and employer PRPP. Signed; zero floor shown separately. The $2,000 excess-contribution cushion is NOT deductible room.',sub(s('deductionLimit'),add(s('openingUnusedContributions'),s('employerPrpp'))))
f('/rrspRoom/additionalContributionSpace','Positive contribution capacity before the new Schedule 7 deposits, excluding any $2,000 excess-contribution cushion.',lo(r('contributionSpaceBeforeNewDeposits')))
f('/rrspRoom/targetYearCapacityAfterReportedContributions','Remaining current-year deduction capacity after the reported deposits, excluding designations and eligible transfers. Includes following-year first-60-day receipts; a negative value is NOT automatically calendar-year excess subject to penalty.',sub(s('personalDeductionRoom'),sub(s('availableToDeduct'),s('eligibleTransfers'))))
f('/rrspRoom/unusedDeductionRoomCarryforward','T4040 Chart 3 step 8: signed calculated pre-floor room less ordinary deduction and employer PRPP, not less transfer deductions. Requires Chart 3 inputs even when using an assessed current limit.',sub(r('unflooredLimit'),add(s('ordinaryDeductionChosen'),s('employerPrpp'))),line='51')
# Next-year Chart 3 reuses the same earned-income and pension-adjustment rules.
# Keep its inputs separate: the existing room worksheet uses PREVIOUS-year income.
import copy
next_prefix='/nextYearRrsp'
def shift_next(expr):
 if isinstance(expr,dict):
  return {k:(val.replace('/rrspRoom','/nextYearRrsp',1) if k=='path' and val.startswith('/rrspRoom') else shift_next(val)) for k,val in expr.items()}
 if isinstance(expr,list):return [shift_next(a) for a in expr]
 return expr
f(next_prefix+'/targetYear','Year whose RRSP deduction limit is estimated: selected return year plus one.',add(year,v(1,'Int')),t='Int',module='nextYearRrsp')
f(next_prefix+'/useCalculatedCarryforward','Use the signed unused deduction room from the current-year T4040 worksheet and Schedule 7? Choose No to enter signed unused room directly.',t='Boolean',module='nextYearRrsp')
f(next_prefix+'/openingUnusedRoom','Signed unused deduction room at the end of the selected return year (Chart 3 step 8 / CRA statement). Include a negative balance; do not enter unused contributions.',module='nextYearRrsp',nonnegative=False)
f(next_prefix+'/openingRoom','Unused deduction room carried into next year, from the current worksheet or your signed input.',switch(d(next_prefix+'/useCalculatedCarryforward'),r('unusedDeductionRoomCarryforward'),d(next_prefix+'/openingUnusedRoom')),module='nextYearRrsp',line='Step 1')
next_names=set(prior)|{'adjustedEmployment','earnedIncome','pensionAdjustment','pensionAdjustmentReversal','exemptPspa','certifiedPspa','qualifyingWithdrawals','newRoom','netPspa','unflooredLimit','estimatedDeductionLimit'}
for original_fact in list(facts):
 if original_fact['path'].startswith('/rrspRoom/') and original_fact['path'].split('/')[-1] in next_names:
  new=copy.deepcopy(original_fact)
  new['path']=new['path'].replace('/rrspRoom','/nextYearRrsp',1)
  new['module']='nextYearRrsp'
  new['formula']=shift_next(new['formula'])
  new['definition']=new['definition'].replace('prior tax year','selected return year').replace('Prior-year','Selected return year').replace('prior year','selected return year').replace('prior-year','selected return year').replace('prior earned','selected return year earned').replace('Current-year','Next-year').replace('current-year','next-year').replace('current year','next year')
  facts.append(new)
f(next_prefix+'/annualDollarLimit','Published RRSP dollar ceiling for the following year; unknown for unsupported years. This caps new room, not total carried-forward room.',op('Switch',case(eq(year,v(2025,'Int')),v(33810)),case(eq(year,v(2026,'Int')),v(35390))),module='nextYearRrsp',line='Step 3')
facts[-1]['authorities'].append(dict(label='CRA annual RRSP limits',pinpoint='2026 and 2027',url='https://www.canada.ca/en/revenue-agency/services/tax/registered-plans-administrators/pspa/mp-rrsp-dpsp-tfsa-limits-ympe.html'))
# Reconcile exact current-return sources; retain only classification adjustments as questions.
n=lambda name:d('/nextYearRrsp/'+name)
f('/nextYearRrsp/employmentIncomeAdjustment','Signed adjustment to employment remuneration plus benefits and option benefits to reconcile Chart 3 line 10100 + 10400. Include other employment amounts recorded elsewhere; enter zero when the existing employment records contain the full total.',module='nextYearRrsp',nonnegative=False)
for root_path,name in [('/otherIncome','supportReceived'),('/subdivisionEDeductions','supportDeducted')]:
 f(root_path+'/*/rrspSupportAmount','Support amount already classified in this return, linked to next-year RRSP earned income.',switch(eq(d(root_path+'/*/category'),v('support','String')),d(root_path+'/*/amount'),v(0)),module='nextYearRrsp',ui={'hidden':True})
links={
 'employmentIncome':(add(*[total('/employments/*/'+key) for key in ['remuneration','benefits','optionBenefits']],n('employmentIncomeAdjustment')),'Linked employment remuneration, taxable benefits and option benefits, plus the explicit line 10400 reconciliation adjustment.'),
 'supportIncome':(total('/otherIncome/*/rrspSupportAmount'),'Linked taxable support records from Other income. Include qualifying support repayments in that category.'),
 'deductibleSupport':(total('/subdivisionEDeductions/*/rrspSupportAmount'),'Linked deductible support records from Subdivision E deductions, including qualifying support repayments.'),
 'athleteTrustIncome':(d('/schedule7/athleteTrustContributions'),'Linked qualifying performance income from Schedule 7 Part F; enter this amount once in Schedule 7.')}
for fact in facts:
 if fact['path'].startswith('/nextYearRrsp/') and fact['path'].split('/')[-1] in links:
  expr,desc=links[fact['path'].split('/')[-1]]
  fact.update(formula=expr,kind='derived',definition=desc)
# Default to the existing signed carryforward. A saved explicit No still permits statement input.
for fact in facts:
 if fact['path']=='/nextYearRrsp/openingRoom':
  use=switch(op('IsComplete',n('useCalculatedCarryforward')),n('useCalculatedCarryforward'),op('True'))
  fact['formula']=switch(use,r('unusedDeductionRoomCarryforward'),n('openingUnusedRoom'))
 if fact['path']=='/nextYearRrsp/useCalculatedCarryforward':
  fact['definition']='Defaults to Yes when unanswered: reuse current T4040/Schedule 7 signed unused room. Choose No only to supply a different CRA statement balance below.'
 if fact['path']=='/nextYearRrsp/openingUnusedRoom':
  fact['definition']='Optional signed CRA unused-room override, used only when Use calculated carryforward is No. Otherwise the earlier T4040 and Schedule 7 values are reused.'
# Chart 3 classification lives with each income source; these are subsets/adjustments,
# not additional taxable-income postings.
source_links={}
for name in ['royalties','researchGrants','supplementaryUnemployment','wageProtection','unionDues','employmentExpenses','employmentIncomeAdjustment']:
 desc=next(x['definition'] for x in facts if x['path']=='/nextYearRrsp/'+name)
 path='/employments/*/'+name
 f(path,desc+' Enter only this record’s portion. This detail does not add income or deduct expenses again; include taxable amounts and deductions in the source totals above.',module='employments',nonnegative=name!='employmentIncomeAdjustment')
 source_links[name]=total(path)
f('/businesses/*/activeForRrsp','Was this business carried on by you alone or as an active partner for RRSP earned-income purposes?',t='Boolean',module='businesses')
f('/businesses/*/athleteTrustDistributions','Amateur-athlete trust distributions included in this business net income. Excluded from RRSP earned income. Enter zero if none.',module='businesses')
f('/businesses/*/eligibleCapitalGains','Taxable eligible-capital-property gains included in this business income for Chart 3 line 25. Enter zero if none. Does not change the business net amount.',module='businesses')
b=lambda name:d('/businesses/*/'+name)
active_net=sub(b('net'),b('athleteTrustDistributions'))
for name,expr in [('rrspIncome',lo(active_net)),('rrspLoss',lo(sub(v(0),active_net))),('rrspEligibleCapitalGains',b('eligibleCapitalGains'))]:
 f('/businesses/*/'+name,'Active-business component of next-year RRSP earned income.',switch(b('activeForRrsp'),expr,v(0)),module='businesses')
f('/properties/*/sourceType','Classify this source: only rent from real property feeds RRSP earned income. Keep investment and rental sources in separate records.',t='String',module='properties',values=['realPropertyRental','otherProperty'])
for name,expr in [('rrspRentalIncome',lo(d('/properties/*/net'))),('rrspRentalLoss',lo(sub(v(0),d('/properties/*/net'))))]:
 f('/properties/*/'+name,'Real-property rental component of next-year RRSP earned income; excludes other property income.',switch(eq(d('/properties/*/sourceType'),v('realPropertyRental','String')),expr,v(0)),module='properties')
source_links.update(businessIncome=total('/businesses/*/rrspIncome'),businessLosses=total('/businesses/*/rrspLoss'),eligibleCapitalGains=total('/businesses/*/rrspEligibleCapitalGains'),rentalIncome=total('/properties/*/rrspRentalIncome'),rentalLosses=total('/properties/*/rrspRentalLoss'))
for fact in facts:
 if fact['path'].startswith('/nextYearRrsp/') and fact['path'].split('/')[-1] in source_links:
  name=fact['path'].split('/')[-1]
  fact.update(formula=source_links[name],kind='derived',definition='Linked from the classified income-source records. Edit the corresponding Employment, Business or Property record to change this amount.')
# Separate posting bridges used by the original income aggregate overlays.
f('/schedules/rrspDeductionPosted','Schedule deduction when enabled; zero otherwise for compatibility with older/manual returns.',switch(active('/schedules/useRrsp'),s('deduction'),v(0)),module='scheduleSetup')
f('/schedules/rrspIncomePosted','Schedule repayment-shortfall income when enabled; zero otherwise.',switch(active('/schedules/useRrsp'),s('shortfallIncome'),v(0)),module='scheduleSetup')
f('/schedules/federalDonationCredit','Schedule 9 federal credit when enabled; existing reviewed manual credit otherwise.',switch(active('/schedules/useDonations'),d('/schedule9/federalCredit'),d('/credits/donations')),module='scheduleSetup')
f('/schedules/claimedGiftsForNs','Shared eligible Schedule 9 claim when enabled; reviewed manual provincial gift amount otherwise.',switch(active('/schedules/useDonations'),d('/schedule9/claimedGifts'),d('/ns/eligibleDonations')),module='scheduleSetup')
# Explicit, derived-only replacements, leaving the standalone foundation files intact.
original=json.loads((out.parent/'catalogue.json').read_text())
replacements=[]
for name,post in [('/income/subdivisionEDeductions','/schedules/rrspDeductionPosted'),('/income/otherSourceIncome','/schedules/rrspIncomePosted')]:
 old=next(x for x in original['facts'] if x['path']==name);new=dict(old);new['formula']=add(old['formula'],d(post));new['definition']=old['definition']+' Includes the enabled Schedule 7 posting exactly once; generic records must exclude that amount.';facts.append(new);replacements.append(name)
def xml(x,root=None):
 attrs={}
 if 'path'in x:
  path=x['path'];attrs['path']=('../'+path.split('/*/')[1]) if root and path.startswith(root+'/*/') else path
 e=E.Element(x['op'],attrs)
 for a in x.get('args',[]):
  if isinstance(a,dict):e.append(xml(a,root))
  else:e.text=str(a)
 return e
root=E.Element('FactDictionaryModule');ff=E.SubElement(root,'Facts')
for ns in ['/schedules','/schedule9','/schedule7','/rrspRoom','/nextYearRrsp']:
 el=E.SubElement(ff,'Fact',path=ns);E.SubElement(E.SubElement(el,'Derived'),'String').text=ns
for x in facts:
 el=E.SubElement(ff,'Fact',path=x['path']);E.SubElement(el,'Description').text=x['definition'];expr=E.SubElement(el,'Derived' if x['formula'] else 'Writable')
 if x['formula']:expr.append(xml(x['formula'],x['path'].split('/*/')[0] if '/*/'in x['path'] else None))
 else:
  E.SubElement(expr,x['type'])
  if x.get('nonnegative'):E.SubElement(E.SubElement(expr,'Limit',type='Min'),'Dollar').text='0'
E.indent(root);E.ElementTree(root).write(out/'fact-dictionary.xml',encoding='utf-8',xml_declaration=True)
(out/'catalogue.json').write_text(json.dumps(dict(version='0.4.0',replaces=replacements,facts=facts),indent=2)+'\n')
print(len(facts),'schedule facts including',len(replacements),'explicit derived aggregate replacements')
