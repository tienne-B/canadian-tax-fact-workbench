# Nova Scotia personal income tax dictionary

A separate provincial module for the IRS Fact Graph engine, linked to the existing Canadian federal foundation. It has **45 provincial domain facts and 12 annual parameter selectors**. With the federal tax extension, the combined app has 373 catalogue definitions. Federal XML and catalogue files remain unchanged.

## Files and references

- `../dictionary-modules.json` is the composition manifest. It references the federal module, this module’s annual selectors and this module’s rules, in dependency order.
- `fact-dictionary.xml` contains provincial inputs and calculations. `catalogue.json` adds definitions, legal pinpoints and form metadata.
- `parameters.xml` selects explicit annual values using `/return/taxYear`; `parameter-catalogue.json` describes those selectors. `parameters.json` records the annual values and sources for review. The runtime uses XML; JSON is the human-readable parameter record. Regenerate them together with `scripts/generate-nova-scotia.py` at the app root.
- `sources.json` records provenance and the SHA-256 of the bundled legislative HTML snapshot, `source-income-tax.html.gz`.

The loader composes the XML in memory because the IRS engine imports a single `FactDictionaryModule`. It rejects duplicate modules and definitions. No provincial definitions are inserted into the federal source files.

Shared dependencies are `/return/taxYear`, `/return/currency`, `/residence/status`, `/residence/provinceAtYearEnd`, `/person/birthDate/year`, `/person/deathDate`, `/person/spouseNetIncome`, `/income/netIncome`, `/taxableIncome/amount`, and `/review/coreReady`. Changing federal facts immediately recomputes provincial dependants in the same native graph. There is no separately editable provincial taxable income.

## Supported scope

The structure is year-independent; numerical packs are explicitly supported for **2025 and 2026 only**. Other years remain incomplete. The ordinary-return scope covers a living natural person resident in Canada throughout the year and Nova Scotia on December 31, with all income allocated to Nova Scotia. Part-year, non-resident, deceased, bankruptcy, separate, trust and multi-jurisdiction business returns require extensions and are not supported by this calculation.

`/ns/taxPayable` is provincial income tax after nonrefundable credits and reviewed adjustments. The NS output itself excludes federal tax, tax withheld, instalments, refundable NS479 credits and balance owing. The separate federal-tax module now combines these into total payable and the final return balance. The frontend also requires the existing return metadata and federal review gates before showing its headline result.

## Implemented calculations

| Calculation | Authority | Treatment |
|---|---|---|
| Progressive tax | ss8,22A | Five brackets, annual thresholds and cumulative base taxes |
| Basic personal | s10B | Annual base, no income phase-out in 2025+ |
| Spouse | ss10C,10J | Eligibility reviewed; shared spouse income reduces annual base |
| Eligible dependant | ss10D,10J | Reviewed base, checked against annual maximum and spouse exclusivity |
| Age | ss10G,22A | Age from federal birth date; 15% phase-out over adjusted income of $30,828; that threshold is not indexed |
| Pension | s10H | Reviewed eligible income capped at $1,173 |
| Other base credits | ss10E–10F,10I,13–19 | Reviewed aggregate after each provincial entitlement and limit; multiplied by 8.79% |
| Medical/naturopath | ss12,12B | Family medical threshold calculated; other dependant/naturopath bases reviewed |
| Donations | s11 | 8.79% first $200, 21% balance of eligible gifts |
| Dividends | s21 | 8.85% taxable eligible and 1.5% taxable non-eligible dividends, including gross-up |
| Special additions, minimum tax | ss9,20,30–31 | Statutory 57.5% factors on specified federal amounts; NS split-income tax separately reviewed |
| Foreign credit | s34 | Reviewed provincial amount after legal limits |
| Low-income reduction | s35 | $300 + qualifying $300 + $165 per other qualifying dependant, less 5% of adjusted family income over $15,000 |
| Age tax credit | s36B | $1,000 for age 65+ and taxable income strictly below $24,000 |
| Certificate credits | ss37–38 | Reviewed usable aggregate after each certificate, annual and carryforward limit |
| Political contributions | s50 | 75%, capped at $750 and available tax |
| Farmer food donations | s50A | 25% of eligible value; checked as included in charitable gifts |

Complex eligibility is deliberately represented as reviewed inputs. The module does not independently determine all caregiver, infirm dependant, disability, tuition, transfer, certificate or foreign-credit entitlements. A yes/no review confirmation does not prove legal eligibility. Do not enter federal credit-dollar amounts as provincial bases.

## Use in the form

1. Enter federal return, income, deductions and personal facts, including date of birth and province `NS`.
2. Open **Nova Scotia · scope**, select the appropriate scope/review decisions, then complete the credits, reduction and tax sections. Enter zero only after confirming an amount does not apply.
3. If not claiming the spouse amount or low-income reduction, choose **No**; the conditional spouse income or reduction detail inputs can remain blank. All other required amounts remain unknown until supplied. An under-65 taxpayer need not supply the age-income adjustment.
4. Complete the federal review confirmations and metadata. The headline provincial tax then appears when the native `/ns/taxPayable` is complete and no validation errors remain.
5. Inspect **Explore graph** for provincial formulas and annual parameters. Export native IRS graph JSON, or nodes/edges with module references.

**Load example** supplies fictional 2025 NS circumstances and zero additional provincial claims. It leaves review attestations unanswered. Its $50,200 taxable income gives $5,625.67 bracket tax less $1,032.30 basic personal credit = **$4,593.37**. Changing the year to 2026 gives $5,595.61 less $1,048.82 = **$4,546.79**, subject to renewed review for that year.

## Sources and annual updates

The primary source is the [Nova Scotia Income Tax Act, R.S.N.S. 1989, c.217](https://nslegislature.ca/sites/default/files/legc/statutes%20HTML/income%20tax.htm), retrieved September 12, 2026. The HTML snapshot has an April 23, 2026 amendment comment (Release 80). Check commencement/application provisions before extending scope.

Annual thresholds and principal personal amounts were checked against the province’s [personal income tax rates and indexation](https://www.novascotia.ca/personal-income-tax-rates-and-indexation). The [2025 CRA Nova Scotia guide](https://www.canada.ca/en/revenue-agency/services/forms-publications/tax-packages-years/general-income-tax-benefit-package/nova-scotia/5003-pc.html) and NS428 support the 2025 calculation order. The 2026 pack uses the Act and published provincial parameters; it has not been checked against a final 2026 NS428 form.

Section 22A indexes eligible amounts using unrounded prior amounts, then rounds to whole dollars. Do not repeatedly index the displayed rounded numbers to create future packs. The 2026 spouse ceiling/floor are derived under s22A. The $30,828 age phase-out threshold, medical threshold, pension cap and s35 amounts are not indexed by this pack.

Calculations use native IRS Dollar arithmetic, including its cent rounding (half-even). Cumulative bracket base taxes are prepared from exact bands before rounding. This is an executable foundation, not CRA-certified filing software; statutory eligibility, rounding reconciliation and return-specific exceptions still require review.

## Validation

Run from the app directory:

```
node tests/engine.test.mjs
node tests/nova-scotia.test.mjs
```

Native-engine checks cover both years’ bracket thresholds and adjacent cents, shared federal-income updates, key credits and reductions, age and spouse boundaries, unsupported years and scopes, inconsistent claims, missing inputs, invalid amounts, duplicate-module rejection and native graph export/restore. The original eleven federal scenarios remain passing.
