# Canadian Tax Fact Workbench

A browser-only interview and native IRS Fact Graph for shared Canadian income facts, Nova Scotia income tax, federal tax, total payable and the calculated balance owing/refund. Supported ordinary-return parameter packs: 2025 and 2026.

See [federal tax and settlement documentation](dist/federal-tax/README.md) and [Nova Scotia documentation](dist/nova-scotia/README.md) for formulas, sources, scope and reviewed inputs.

Choose **Federal credits → Credit input basis → Claim amounts** for ordinary pre-rate claim amounts. Donations and top-up remain final credit dollars. Choose **Credit dollars** for older entries that are already tax reductions.

## Donations and RRSP schedules

Enable Schedule 9 and/or Schedule 7 under **Schedule options**. See [Schedules 7, 9 and T4040 documentation](dist/schedules/README.md) for donation elections/carryforwards, shared federal/NS credits, RRSP room, contributions, transfers and repayments. Schedule 7 posts reviewed deductions and shortfall income automatically; remove duplicate generic entries first.

## Run

Serve `dist/` over HTTP, for example `python3 -m http.server 4173 --directory dist`. Open the local URL. Export current values before reloading: values are held only in page memory. No analytics, server storage or transmission of entered values is implemented.

Twenty interview sections and a graph explorer expose 373 catalogue definitions. Separate dictionary files are loaded by `dist/dictionary-modules.json` and composed in memory. Exports support native IRS graph JSON and concrete nodes/edges with module references.

## Import saved answers

Click **Import JSON**, choose either a native fact-graph export or a nodes-and-edges export from this app, then confirm the replacement preview. Import replaces the current answers; cancel to keep them. Export first if you want a backup.

Files are read locally (maximum 10 MB). Types, fact paths and collection membership are checked before any answers change. Unknown or calculated input paths are rejected. Calculated nodes in a nodes-and-edges export are ignored and recomputed from its `inputs`. Saved legal review confirmations are cleared so the current dictionaries are reviewed again; ordinary answers, zero/false values and collection identifiers are preserved. Older exports can leave newly added fields unanswered.

## Validate

```
node tests/engine.test.mjs
node tests/nova-scotia.test.mjs
node tests/federal-tax.test.mjs
node tests/import-graph.test.mjs
node tests/schedules.test.mjs
```

All three suites use the compiled IRS Scala.js engine. Static checks also verify form IDs, local asset references and JavaScript syntax. No browser visual QA was performed for this extension.

## Structure

- `dist/catalogue.json` and `dist/fact-dictionary.xml`: original federal income foundation, unchanged.
- `dist/nova-scotia/`: NS rules, annual parameters and source snapshot.
- `dist/schedules/`: Schedule 9, Schedule 7, T4040 room and explicit derived-income overlays.
- `dist/federal-tax/`: federal tax and settlement formulas, annual parameters and sources.
- `dist/dictionary-loader.mjs`: reference loading and duplicate-definition checks.
- `dist/engine.mjs`: native graph adapter and input/consistency validation.
- `dist/app.mjs`: generated form, summaries and graph explorer.
- `scripts/`: reproducible provincial and federal tax dictionary generators.
- `dist/vendor/factgraph.mjs`: IRS-Public/fact-graph commit prefix 5599f75, compiled with Scala 3.3.6 / sbt 1.11.4 / JDK 17; upstream license alongside it.

The supported ordinary-return scope and review gates are explicit. Complex entitlement and schedule calculations remain reviewed inputs; this is not certified filing software or a CRA account balance. See the module documentation for cent-rounding behaviour and unsupported return types.
