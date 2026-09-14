# Schedule 9, Schedule 7 and T4040 RRSP room

The separate schedules module adds 116 new definitions and explicitly extends two existing derived income totals. The combined app has 373 catalogue definitions. All numerical formulas run in the native IRS engine.

## In the form

1. Open **Schedule options** and enable **Use donations**, **Use RRSP**, or both. Older saved graphs continue using their manual entries until a schedule is enabled.
2. Complete **Donations & gifts**, **RRSP room · T4040** and/or **RRSP · Schedule 7** as applicable. Explicitly enter zero or confirm an empty collection when nothing applies.
3. Complete the schedule review confirmations. Enabling Schedule 7 also clears the shared deduction review. Changing the tax year clears schedule reviews. Importing a saved graph preserves answers but clears reviews.
4. Inspect calculated schedule outputs and their downstream federal/provincial tax effects in the graph.

While enabled, Schedule 9 replaces the use of the manual federal donations-credit and NS eligible-donations inputs. The form displays the linked results in those locations. Schedule 7 posts its deduction and repayment-shortfall income automatically. **Remove the same RRSP deduction and HBP/LLP shortfalls from generic deduction and income records first**; receipt descriptions alone cannot reliably identify duplicates. Ordinary RRSP withdrawals and other unrelated amounts still belong in their existing income records.

The original manual fields are retained for backward compatibility, with saved manual values ignored while their schedule is enabled. Turning a schedule off returns to manual handling. Schedule calculations do not silently change claim elections or overwrite saved answers.

## Donations and Gifts — Schedule 9

Create a gift pool for each origin year/category, recording the remaining eligible amount and the portion elected for this return. Categories cover the ordinary qualified-donee groups and separately certified cultural/ecological gifts. The ledger tracks ordinary five-year and ecological ten-year expiry, remaining carryforwards and unclaimed amounts expiring this year.

Prior claims and spouse allocations must already be removed from the available amount. In particular, a Jan–Feb 2025 gift used on the 2024 return must not be claimed again. Review oldest-first usage and recipient/certificate eligibility. The module does not optimize how spouses allocate claims or how much to defer.

The ordinary claim limit is the lesser of net income and 75% of net income plus 25% of the qualifying capital-gift amounts. A class-level depreciable-property chart takes the lesser of gift-related recapture and the class's aggregated eligible property amount. The latter is a reviewed sum of each property's lesser net proceeds/capital cost. The separate capital-gains chart subtracts the related capital-gains deduction from taxable gains. Capital gains/recapture themselves must already be included once in the appropriate income records.

The federal calculation splits the elected gifts into:

- First $200 at the annual lowest rate (14.5% in 2025; 14% in 2026).
- The qualifying portion above $200 at 33%, limited by taxable income above the top-bracket threshold.
- The remaining portion above $200 at 29%.

Ecological gifts originating before 2016 are excluded from the 33% portion; the 2015 carryforward can still be relevant in 2025. NS applies 8.79% to the first $200 and 21% to the balance of the **same elected eligible gifts**. Its additional farmer-food credit stays separate, and the food amount must fit within the shared gift claim.

Key paths:

| Path | Result |
|---|---|
| `/schedule9/ordinaryLimit` | Income-based ordinary gift ceiling |
| `/schedule9/claimedGifts` | Validated, reviewed election shared with NS |
| `/schedule9/federalCredit` | Schedule 9 / federal line 34900 |
| `/schedule9/novaScotiaCredit` | Ordinary NS donation credit |
| `/schedule9/carryforward` | Remaining gifts with future claiming years |
| `/schedule9/expiredUnclaimed` | Unclaimed gifts expiring or already expired |

Claims above available pools, future-dated claims, expired positive claims, excess ordinary claims and inconsistent capital-gift amounts block the reviewed result. Cultural/ecological claims are outside the ordinary income ceiling. Foreign university/registered foreign charity eligibility requires review; treaty-specific US gifts, deceased/estate rules and other exceptional gift treatments need an external determination or further extension.

## RRSP — Schedule 7

The workflow covers Parts A–F using reviewed contribution totals rather than importing brokerage receipts:

- Opening contributions previously reported but not deducted.
- Own and spousal contributions separately for the main reporting period and the following year's first 60 days.
- HBP/LLP designations and required repayments, excluding spousal amounts from the repayment pool.
- Employer PRPP contributions and eligible taxable-income transfers.
- Maximum ordinary deduction, the amount elected, total deduction and unused contribution carryforward.
- HBP/LLP withdrawal/activity and amateur-athlete trust reporting facts.

For the 2025 return, the main period is March 4–December 31, 2025 and the following reporting period ends March 2, 2026. The 2026 pack uses March 3–December 31, 2026 and January 1–March 1, 2027; that calendar-derived timing has not been reconciled with a final 2026 Schedule 7. Contributions in the selected year's first 60 days already reported on the previous return belong in opening unused contributions if still available, not again in the main-period fields.

The maximum ordinary deduction is the lesser of the selected deduction limit less employer PRPP, and contributions available after designations and transfers. The elected deduction may be lower; eligible transfers are added separately. Designated repayments are not deductible. HBP/LLP required amounts less designated repayments become taxable shortfalls; qualifying Part E withdrawals do not become ordinary income merely because they were recorded here.

Required HBP/LLP repayments come from the CRA statement, including any repayment deferral. They are not inferred from the withdrawal alone. Own-plan contribution and transfer eligibility, age limits, the 90-day withdrawal restriction, contribution refunds, direct tax-deferred transfers, exempt earnings and other exclusions are reviewed input responsibilities. Separate exceptional withdrawal/cancellation treatments are not automatically computed.

| Path | Result |
|---|---|
| `/schedule7/deductionLimit` | Selected assessed limit or T4040 estimate |
| `/schedule7/maxOrdinaryDeduction` | Maximum ordinary deduction excluding transfers |
| `/schedule7/deduction` | Schedule 7 line 20 / T1 line 20800 |
| `/schedule7/unusedContributionsCarryforward` | Contributions not yet deducted |
| `/schedule7/shortfallIncome` | HBP/LLP shortfalls for line 12900 |

## RRSP space — T4040 Chart 3

The estimator uses the **previous** year's inputs, not current taxable income. It implements the chart's employment adjustment and other earned-income inclusions/losses, annual new-room cap, PA (including reviewed prescribed/foreign adjustments), PAR and signed net PSPA. Opening unused deduction room can be reconstructed from the prior limit/deductions/employer PRPP or entered directly, including a negative opening balance.

The RRSP dollar ceiling is $32,490 for 2025 and $33,810 for 2026. New room is the lesser of 18% of prior earned income and the ceiling, less PA, floored at zero. Opening room and PAR are added and net PSPA is subtracted. The personal deduction limit is floored at zero, while the signed pre-floor amount is retained for Chart 3's unused-room carryforward.

Select **CRA assessment** to use `/registeredPlans/rrspDeductionLimit`, or **T4040 estimate** to use the calculated result. The latter is an estimate requiring reconciliation with the latest assessment/T1028, especially after reassessments or unusual pension adjustments.

| Path | Meaning |
|---|---|
| `/rrspRoom/estimatedDeductionLimit` | Chart 3 calculated current-year limit |
| `/rrspRoom/contributionSpaceBeforeNewDeposits` | Signed selected limit less opening unused contributions and employer PRPP |
| `/rrspRoom/additionalContributionSpace` | Positive part of that capacity, before the newly reported deposits/designations |
| `/rrspRoom/targetYearCapacityAfterReportedContributions` | Signed current-year capacity after all Schedule 7 deposits, excluding designations and eligible transfers |
| `/rrspRoom/unusedDeductionRoomCarryforward` | Chart 3 signed room after ordinary deductions/employer PRPP; transfers excluded |

The $2,000 excess-contribution cushion is not included as contribution room or deductible capacity. A negative capacity result does not itself calculate excess-contribution tax. In particular, the Schedule 7 reporting window includes deposits made in the next calendar year; those may use that next year's room. Monthly T1-OVP analysis, withdrawals/refunds, contribution timing and applicable exceptions require a separate calculation. Room also does not establish eligibility to contribute to a particular own/spousal plan after its age deadline.

## Integration and validation

`dictionary-modules.json` loads this module by reference. The loader permits only explicitly listed replacements of existing **derived** facts: `/income/subdivisionEDeductions` adds the enabled RRSP deduction, and `/income/otherSourceIncome` adds enabled repayment-shortfall income. Their original standalone XML/catalogue files are unchanged. Undeclared duplicates and attempts to replace writable facts are rejected. The full composed bundle is required for the new cross-module references.

Donation limits and tiers reference the resulting net/taxable income, so RRSP changes flow through to the gift ceiling, federal tax, NS tax and settlement. Federal donations remain outside the ordinary nonrefundable-credit rate. Amounts use the native engine's cent rounding; see the federal module documentation for rounding conventions and filing limitations.

Run `node tests/schedules.test.mjs` plus the existing income, NS, federal-tax and import suites. Tests include both years, ordinary/cultural/ecological gifts, the 33% tier, old ecological carryforwards, expiry, capital boosts, signed RRSP room, PA/PAR/PSPA, transfers, repayments, elected deductions, automatic posting, the RRSP/donation-limit interaction, review/import gates and all original federal scenarios in the composed dictionary.

## Sources

- [CRA Schedule 9, 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s9/5000-s9-25e.txt)
- [CRA Schedule 7, 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s7/5000-s7-25e.txt)
- [T4040, RRSPs and Other Registered Plans for Retirement](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4040/rrsps-other-registered-plans-retirement.html), Chapter 2 and Chart 3
- [CRA annual registered-plan limits](https://www.canada.ca/en/revenue-agency/services/tax/registered-plans-administrators/pspa/mp-rrsp-dpsp-tfsa-limits-ympe.html)
- [Nova Scotia Income Tax Act](https://nslegislature.ca/sites/default/files/legc/statutes%20HTML/income%20tax.htm), s11

The retrieved Schedule 7/9 and T4040 snapshots and hashes are recorded in `sources.json`. The 2026 formulas use the published annual parameters with the 2025 schedules' structure; final 2026 form changes remain to be verified. Source-driven formulas are generated by `scripts/generate-schedules.py`; the federal and NS generator scripts contain the bridge references.

### Next-year RRSP estimate

“Review & calculations” includes `/nextYearRrsp/estimatedDeductionLimit`, a separate T4040 Chart 3 worksheet for the selected return year plus one. Enter the selected return year's earned-income components and PA/exempt PSPA, and the following year's expected PAR, certified PSPA and qualifying withdrawals. Inputs are explicit: missing adjustments do not silently become zero. Opening signed unused deduction room can be entered from the CRA statement or linked to `/rrspRoom/unusedDeductionRoomCarryforward` (which requires the current Chart 3 and Schedule 7 inputs). Unused contributions are not unused deduction room.

The following-year dollar ceilings are $33,810 for 2026 and $35,390 for 2027, from [CRA annual limits](https://www.canada.ca/en/revenue-agency/services/tax/registered-plans-administrators/pspa/mp-rrsp-dpsp-tfsa-limits-ympe.html). Unsupported years remain incomplete. The estimate preserves signed opening room and net PSPA, floors new room after PA and the final deduction limit at zero, and does not change the current return's deduction or tax. Compare the estimate with CRA's assessment.


#### Reconciliation with existing return inputs

Employment records now hold the Chart 3 special employment components, dues, expenses, and a signed reconciliation adjustment. These are detail amounts, not additional taxable income or deductions. Business records identify active participation, athlete-trust distributions excluded from earned income, and eligible-capital-property gains. Property records distinguish real-property rentals from other property income. Next-year RRSP totals aggregate those records, preserving rental/business losses and excluding investment income. Missing classifications remain unknown; confirmed empty collections contribute zero.

Taxable and deductible support are linked by category, athlete-trust contributions from Schedule 7 Part F, and opening unused room defaults to the signed current-year T4040/Schedule 7 carryforward. A CRA statement override remains available. CPP/QPP disability, postdoctoral income and year-specific pension adjustments still require separate evidence.

RRSP is no longer a Subdivision E deduction option: enter it through Schedule 7. Imports containing that old category stop with a migration instruction so deductions are neither silently deleted nor counted twice. Superseded standalone next-year inputs are discarded with notices and recalculated from source records; fill missing source details after importing.
