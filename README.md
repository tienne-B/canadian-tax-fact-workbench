# Canadian Tax Fact Workbench

A static, dictionary-driven frontend using the actual IRS Fact Graph 3.1 Scala.js engine. Nine interview sections expose all 133 domain definitions, with typed controls, repeated records, explicit unknown/empty distinctions, legal links, and an interactive dependency neighbourhood for any concrete fact.

Values exist only in page memory. There is no analytics, server storage, localStorage or third-party value submission. Reloading clears the interview. Export fact graph downloads the native IRS persister JSON. Export nodes & edges adds concrete nodes, dependency links, input values and review state for external graph tools.

## Run locally

Serve `dist/` using any static HTTP server. For example, `python3 -m http.server 4173 --directory dist`. ES modules require HTTP; opening index.html as a file is not supported.

## Validate

Run `node tests/engine.test.mjs`. Eleven original arithmetic scenarios run against the compiled native engine. Additional checks cover input types/limits, ABIL consistency, unknown versus explicitly empty collections, and native JSON round trips.

## Structure

- `dist/app.mjs`: dictionary-driven interview, graph explorer and exports.
- `dist/engine.mjs`: native IRS engine adapter, typed input validation and host consistency checks.
- `dist/catalogue.json`: the 133 domain facts and legal provenance.
- `dist/fact-dictionary.xml`: native XML, with 13 derived String namespace constants necessary to resolve nested paths. Namespace constants are infrastructure, not questions.
- `dist/vendor/factgraph.mjs`: compiled from IRS-Public/fact-graph commit prefix 5599f75 using `factGraphJS/fullLinkJS`, Scala 3.3.6 / sbt 1.11.4 / JDK 17.
- `dist/vendor/IRS-LICENSE.md`: upstream license.

The JSGraph `set` API saves values on each call. Collections use its native collection methods. Do not add a `graph.save()` call: the current browser export does not expose that method. GraphFactory.fromJSON(dictionary, exportedJSONString) restores native exports in integrations.

## Scope

Core section 3 and ordinary-resident taxable-income arithmetic only. Credits and benefits are external-determination contracts, not implemented entitlement rules. Summary results remain hidden until review and return metadata are supplied; the graph inspector explicitly exposes arithmetic for debugging. A review attestation does not replace legal review. The year field does not select a legal version automatically. See catalogue source metadata for the June 2026 XML / July 2026 HTML consolidation-date discrepancy.

Manual verification: load the fictional example; inspect `/taxableIncome/amount` ($50,200); change remuneration from $60,000 to $61,000 and inspect $51,200; add/remove a record; clear an input and observe incomplete calculations; export the graph. No user financial values are included in the source or deployment.
