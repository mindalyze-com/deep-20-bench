# Crowdfunded Model Runs

## What we want to achieve

Deep20Bench should let its community propose additional models and collectively fund the cost of
benchmarking them.

The intended experience is:

- Several approved models may seek funding at the same time.
- Every model has its own clearly identified funding pot and target.
- People may contribute small amounts such as $5, $10, or $20.
- Contributions from multiple people accumulate until the run is fully funded.
- Everyone can see the current total and progress without the maintainer updating it manually.
- Reaching the target schedules the exact preregistered model configuration for execution.
- Every completed result is published, whether the model performs well or poorly.
- Funding covers provider costs, transaction fees, and reasonable cost variance so the
  maintainer does not have to subsidize community-requested runs.
- Financial participation never gives a supporter influence over subjects, prompts,
  adjudication, scoring, publication, or benchmark internals.

The system should remain simple enough for small campaigns of roughly $50 to $60 while being
transparent and trustworthy for contributors.

## Summary

Deep20Bench can let the community suggest and jointly fund public benchmark runs. Each approved
model receives its own funding pot, allowing several supporters to combine small contributions
such as `$10 + $20 + $20`.

The result must always be public, regardless of its score. Funding pays for a documented
benchmark execution attempt, not for a particular outcome.

## Proposed funding model

1. A community member suggests a model.
2. The maintainer verifies that the model and provider configuration are compatible with the
   benchmark.
3. The exact immutable model configuration and its `M-…` ID are published before funding opens.
4. The model receives a dedicated funding pot with a visible target.
5. Supporters contribute at least $5, with $10 and $20 presented as the recommended amounts.
6. When the combined contributions reach the target, funding closes.
7. The maintainer executes the benchmark and publishes its execution ID, result, actual cost,
   and publication-eligibility status.

For a run expected to cost $50, the initial funding target should be $60. The additional amount
covers payment fees and normal cost variance.

## Polar option

Polar is a potential payment provider because it supports:

- One-time, pay-what-you-want products with a configurable minimum.
- A separate product and checkout link for each approved model.
- Swiss payouts.
- Receipts and invoices.
- International sales-tax handling as merchant of record.
- APIs and webhooks that can support later automation.

### Important Polar restriction

Polar's public product and checkout pages do not currently provide a public cumulative donation
total, funding goal, or progress display such as `$30 / $60`.

The complete order history, revenue, and account balance are visible to the project owner in the
private Polar dashboard. A supporter following a Polar checkout link can see the product and
make a payment, but cannot see how much the community has already contributed toward that
model's run.

Consequently, a Polar link alone is not sufficient for transparent pooled funding. Do not
describe Polar as providing public campaign totals or progress bars unless Polar adds and
documents that capability.

### Required public funding page

Using Polar for parallel funding pots requires a separate Deep20Bench funding page:

1. Each approved model has a Polar product and stable internal funding-pot ID.
2. Polar accepts the payments.
3. A signed Polar webhook reports paid, refunded, and disputed orders to a small hosted service.
4. The service aggregates only the amounts assigned to each funding pot.
5. The public page displays the model, exact configuration, amount raised, target, percentage,
   status, and eventual result link.
6. Supporter names and payment details remain private unless a supporter explicitly opts into
   attribution.
7. When the target is reached, the product is archived or otherwise closed to new contributions
   as soon as practical.

This page must update automatically. The maintainer should not have to update GitHub after every
contribution. GitHub may still be used for source code, model suggestions, and published results,
but it is not the payment ledger.

The Polar API token and webhook secret must remain server-side. The public page must expose only
aggregated funding data and must never expose customer records, email addresses, invoices,
payment identifiers, access tokens, or webhook payloads.

### No-build alternative

If Deep20Bench does not build the automated public funding page, Open Collective Projects is the
preferred alternative. Open Collective provides public balances, contributions, goals, updates,
and expenses for each project without a custom tracker.

This convenience comes with higher costs and onboarding requirements. Open Source Collective
currently charges a 10% host fee in addition to payment-processor fees and expects an eligible,
properly licensed open-source project with suitable governance.

Ko-fi is not suitable for several simultaneous model pots because it supports only one active
goal and cannot reliably earmark individual payments among multiple goals.

## Money rules

- The minimum contribution is $5.
- The interface should recommend $10 and $20 because fixed transaction fees make very small
  payments inefficient.
- The target is the forecast provider cost plus 20%, rounded up to the next $5.
- Contributions remain assigned to the selected model until its pot is funded, cancelled, or
  refunded.
- A pot expires after 120 days unless the maintainer publishes a justified extension.
- When a pot expires, contributors receive a refund or may explicitly request a transfer to
  another pot. Funds must not be silently reassigned.
- If the model becomes unavailable or fails compatibility checks before execution, contributors
  are refunded.
- Once execution starts, funding covers the documented execution attempt rather than a
  successful or favorable result.
- One replacement execution may be funded only after an infrastructure-caused,
  publication-ineligible run. A poor score or model failure never justifies a paid rerun.
- Contributors are never charged again if actual costs exceed the target.
- Surplus after fees and actual execution costs supports anchor-model reruns and future benchmark
  infrastructure. This must be disclosed before payment.
- Supporter identity is private by default and published only with explicit consent.

## Benchmark integrity

Payment handling must remain completely separate from benchmark execution.

- Funding data must not enter `BenchmarkRequest`, prompts, provider requests, model-visible
  messages, sessions, cache namespaces, adjudication, retries, or scoring.
- Sponsors cannot choose hidden subjects, modify the approved configuration, see privileged
  component state, suppress results, or buy a favorable rerun.
- Never accept supporter-provided API keys or provider accounts.
- Model calls use only project-controlled credentials and exact approved routes.
- Funding status may be linked to an execution ID only outside the model-call path or after all
  relevant model calls have completed.
- The first version should not add funding fields to benchmark manifests or typed benchmark
  results. The public funding system links to completed execution IDs externally.
- Any later integration touching reports, artifacts, or automation must use strict typed models
  and include tests proving that the Guesser-visible projection remains unchanged.

## Pilot and acceptance checks

Begin with no more than three simultaneous model pots.

Before launch, verify:

- Multiple supporters can contribute different amounts to the same Polar product.
- Payments cannot be attributed to the wrong funding pot.
- Paid, refunded, and disputed webhook events update totals idempotently.
- The public total reconciles with Polar orders while excluding taxes and clearly defining
  whether the displayed amount is gross or net of fees.
- Replayed or forged webhooks cannot increase the public total.
- Reaching a target closes the pot without losing or hiding any excess contribution.
- Refunds reduce the public total correctly.
- Swiss payouts, invoices, receipts, exports, and accounting records work as expected.
- No funding or customer information appears in Guesser, Oracle, Reviewer, Judge, or Guess
  Validator requests, cache keys, sessions, logs, audits, or errors.

The pilot should remain manual with respect to approving models and starting runs. Payment
reconciliation and public progress updates should be automated before accepting parallel public
funding.
