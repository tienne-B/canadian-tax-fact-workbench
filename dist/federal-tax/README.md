# Federal tax, total payable and refund dictionary

This module adds 67 facts (including 17 annual parameter selectors) to the shared native IRS graph. The full app loads 373 catalogue definitions from separate referenced modules. It calculates federal tax for ordinary full-year Nova Scotia resident returns in 2025 and 2026, combines it with `/ns/taxPayable`, and reconciles payments and refundable credits.

## Credit input correction (0.3.1)

In **Federal credits**, choose **Credit input basis → Claim amounts** when entering the ordinary claim amounts from the return. The calculation is now:

`nonrefundableCredits = round(ordinaryClaimAmounts × nonrefundableCreditRate) + donationsCredit + topUpCredit`

The rate is 14.5% for 2025 and 14% for 2026. Donations and top-up remain final credit dollars outside that multiplication. Dividend, foreign and political credits also remain final credit dollars applied at their later return stages. The basic personal override follows the chosen basis; leaving it blank uses the automatic base/credit as appropriate.

Choose **Credit dollars** only when the ordinary fields already contain calculated tax reductions, as specified by the earlier interface. Older saved graphs have no input-basis fact; their federal calculation stays incomplete until you explicitly choose the correct interpretation. Import does not guess or convert your amounts. Changing the basis clears the federal return review.

Regression example: $16,000 basic-personal base + $1,000 employment amount, multiplied by 14.5%, plus $250 donations credit and $25 top-up = $2,740 of nonrefundable credits. At $50,200 taxable income, this leaves $4,539 basic federal tax before any dividend credit or AMT carryover.

The optional [schedules module](../schedules/README.md) now calculates Schedule 9 donations and posts Schedule 7 RRSP deductions/repayment shortfalls. When enabled, its outputs replace the corresponding manual handling described below.

## Calculation sequence

| Output | CRA line / role |
|---|---|
| `/federalTax/taxOnTaxableIncome` | Step 5 Part A, progressive tax using shared `/taxableIncome/amount` |
| `/federalTax/basicPersonalBase` | 30000, income-dependent basic personal amount |
| `/federalTax/basicPersonalCredit` | Automatic base × lowest rate, or optional reviewed `/credits/basicPersonal` override |
| `/federalTax/nonrefundableCredits` | 35000, total nonrefundable credit dollars, including donations/top-up after the rate |
| `/federalTax/basicFederalTax` | 42900, bracket tax + TOSI − nonrefundable credits − dividends − AMT carryover, floored at zero |
| `/federalTax/federalTaxAfterForeignCredit` | 40600, foreign credit, investment recapture and logging credit applied in return order |
| `/federalTax/regularTaxAfterCredits` | Regular 41700, less political/investment/labour-sponsored credits, floored at zero |
| `/federalTax/taxAfterCredits` | 41700, regular calculation or final T691 replacement amount |
| `/federalTax/netFederalTax` | 42000, 41700 + advanced CWB + special taxes on 41800; review gated |
| `/federalTax/totalPayable` | 43500, federal + NS tax + CPP/EI payable + OAS/EI repayment |
| `/federalTax/totalCreditsAndPayments` | 48200, withholding + instalments + refundable credits/overpayments |
| `/federalTax/netPayable` | Signed difference, 43500 − 48200 |
| `/federalTax/amountOwing` | 48500, positive balance only |
| `/federalTax/refund` | 48400, magnitude of negative balance only |

The total-payable and balance outputs depend on the reviewed NS output. Net federal tax can be inspected independently of the provincial review. A minimum-tax carryover mismatch between federal and NS inputs blocks the combined result. A positive NS additional minimum tax while the federal T691 switch is No also blocks it.

## Form use

1. Complete shared income and deduction facts and choose tax year 2025 or 2026.
2. In **Federal credits**, select the input basis and enter either ordinary **claim amounts** before the rate or already-calculated **credit dollars**, consistently. Donations/top-up always use credit dollars. Leave **Basic personal** blank for automatic calculation; an explicit value overrides it. All other named credits need a value or confirmed zero. The new other-nonrefundable field covers credit categories absent from the original catalogue, after their rates and limits.
3. In **Federal tax**, enter signed basic-personal income adjustments (zero if none), special-schedule values and scope/review decisions.
4. In **Other tax & filing**, enter tax withheld, instalments, TOSI, minimum-tax carryover and OAS recovery. Select T691 under Federal tax only when its reviewed **final line 41700** amount has been supplied in Minimum tax. It replaces regular tax; it is not added to it.
5. Complete Nova Scotia tax and the **Refundable credits** section. Refundable provincial NS479 credits are separate from NS428 tax reductions.
6. Complete the shared review and return metadata. The new summary shows net federal tax, total payable, credits/payments and amount owing/refund. **Balance owing / refund** provides the full dependency breakdown.

Changing the tax year clears annual, NS and federal return-review confirmations. No financial values are stored outside the tab. Export before refreshing or closing it.

## What is calculated versus reviewed

Annual progressive tax, basic-personal phase-out/credit, credit totals, statutory calculation order, combined payable and the final signed balance are executable XML formulas. Credit eligibility, donations, dividends, employment credit, top-up, transfers, foreign credits, contribution schedules, repayments, AMT, refundable credits and other special schedules remain reviewed inputs. Existing credit fields feed federal tax according to the explicit input basis.

For ordinary returns the automatic basic-personal calculation uses adjusted net income. The maximum/minimum bases are $16,129/$14,538 in 2025 and $16,452/$14,829 in 2026. The phase-out interval is the fourth federal bracket. The implementation multiplies before dividing to avoid rounding the phase-out fraction prematurely.

The original IRS engine uses half-even cent rounding for Dollar operations. The automatic basic-personal credit corrects downward half-cent ties to half-up using exact integer arithmetic within the bounded personal-amount range. Other native operations retain IRS rounding; independently rounded credit-dollar inputs and bracket edge cases can differ by a cent from a full CRA base-amount worksheet. Enter reconciled credit dollars where needed. This is not certified filing software.

No automatic dividend income/gross-up integration was introduced by this extension: dividends must still be included once in the property-income facts and supplied as the relevant reviewed credit dollars. Provincial dividend-credit inputs remain separate. Taxes reported on separate registered-plan returns, Part XIII returns, Quebec abatement, foreign/multi-jurisdiction surtax, non-resident, deceased, bankruptcy, separate and trust returns are outside the supported scope. The refund is a calculated return result, not an assessed or issued refund; arrears, interest, penalties and account offsets are excluded.

## Verified example

Fictional 2025 return: taxable income $50,200; only the basic personal credit; NS basic credit only; no contribution liabilities, repayments or refundable credits; $10,000 withheld.

- Federal bracket tax: $7,279.00
- Federal nonrefundable credits: $2,338.71
- Net federal tax: $4,940.29
- NS tax: $4,593.37
- Total payable: $9,533.66
- Credits/payments: $10,000.00
- Calculated refund: **$466.34**

The example intentionally leaves review confirmations unanswered and does not infer an employment credit or CPP/EI eligibility from the fictional wages. Enter those entitlements after review for an actual return.

## Sources and regeneration

- [CRA 2025 T1 return text](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-r/5000-r-25e.txt): Step 5 Parts A–C and Step 6 calculation order and line mappings. Retrieved September 12, 2026; snapshot and hash in this module.
- [Income Tax Act](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/FullText.html): ss117–118.9,120.2,120.4,121,126–127.55,153,156,164 and applicable special/refundable provisions.
- [CRA basic personal amount](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-30000-basic-personal-amount.html): 2025 limits and phase-out.
- [CRA tax rates](https://www.canada.ca/en/revenue-agency/services/tax/individuals/tax-rates-brackets.html) and [2026 federal parameters](https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4032-payroll-deductions-tables/t4032oc-jan/t4032oc-january-general-information.html): 2026 thresholds, rates and personal amounts. Payroll approximation constants are not used; cumulative base taxes are computed from exact bands.
- [CRA line 41700](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/deductions-credits-expenses/line-41700-minimum-tax.html): T691 replaces the regular line 41700 result.

The 2026 pack uses published annual parameters with the 2025 return sequence. Final 2026 return-form changes have not been verified. Unsupported years remain incomplete.

Run `python3 scripts/generate-federal-tax.py` from the app directory to regenerate XML, catalogue and annual parameter documentation together. `dist/dictionary-modules.json` loads this module by reference after federal income and Nova Scotia definitions.

Run `node tests/federal-tax.test.mjs` alongside the existing federal-income and Nova Scotia tests. Checks cover annual brackets, phase-out, optional override versus unknown, credit ordering, zero floors, T691 replacement, contributions, overpayments, all three balance outcomes, review/scope/missing-input gates and native graph export/restore.
