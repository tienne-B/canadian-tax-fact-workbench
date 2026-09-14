# Validation — September 12, 2026

- Original 11 federal-income native-engine scenarios pass.
- Nova Scotia native-engine checks for 2025/2026 remain passing.
- Federal-tax and settlement checks pass: annual brackets and BPA phase-out, optional credit override, credit ordering and zero floors, T691 replacement, combined NS tax, contributions/repayments, refundable credits, owing/refund/zero balance, missing-input/review/scope/consistency gates and native export/restore.
- Combined catalogue has 373 definitions. Original federal income XML and catalogue are byte-for-byte unchanged.
- JavaScript syntax, static form IDs, local assets and XML structure pass. No browser visual QA was performed for this change.
- Local deliverable complete. Publishing remains blocked by the unresolved earlier automatic approval rejection of the source upload.

- Import checks pass for native and nodes/edges exports, typed values and collections, review reset, recomputation, invalid-file rejection and non-mutation of existing answers.

- Credit-basis regression tests cover ordinary claim totals, annual percentage application, donations/top-up exclusion, basic federal tax, legacy credit-dollar compatibility and missing-basis incompleteness.

- Schedule 9 / Schedule 7 / T4040 tests pass, including shared federal/NS donations, expiry, 33% ecological exceptions, RRSP room and signed adjustments, repayments/transfers without double allocation, automatic posting, RRSP/donation-limit interaction and derived-only overlays. All original income scenarios also pass in the composed dictionary.
