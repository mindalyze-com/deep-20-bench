# Crowdfunded Model Runs

Status: proposal only. The site links to general Ko-fi support; it does not implement
model-specific funding pots, a payment ledger, or automatic funded-run scheduling. The rules
below describe a possible future system. Provider suitability was reviewed on 7 September 2026.

## What we want to achieve

Deep20Bench should let its community propose additional models and collectively fund the cost of
benchmarking them.

The intended experience is:

- Several approved models may seek funding at the same time.
- Every model has its own clearly identified funding pot and target.
- People may contribute small amounts such as $5, $10, or $20.
- Contributions from multiple people accumulate until the run is fully funded.
- Everyone can see the current total and progress without the maintainer updating it manually.
- Reaching the target makes the exact preregistered configuration ready for a maintainer to run.
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

## Provider assessment - 7 September 2026

Polar is not an option for the funding model described here under its published policy.
Its acceptable-use policy, effective 25 March 2026, prohibits donations, crowdfunding, and
sponsorship. The earlier proposal to use Polar products and webhooks for model pots is
withdrawn. Pay-what-you-want pricing does not establish permission for this use case.
See [Polar's acceptable-use policy](https://polar.sh/legal/acceptable-use-policy).

Open Collective Projects supports separate public budgets, contributions, expenses, goals,
and updates. It is a possible platform to assess, not a selected host or an approved account.
See [Open Collective's project features](https://documentation.opencollective.com/why-open-collective/features).

Open Source Collective is one fiscal host on that platform. Its application lists a 10% host
fee, and payment-processor fees are separate. Its software-project eligibility requires an
open-source license. Deep20Bench's PolyForm Noncommercial software licensing does not meet
that requirement, so the earlier recommendation of this host is not suitable as written.
Any future platform/host selection must fit the project's existing licensing and proposed
activity. See [host fees](https://opencollective.com/opensource/apply/intro),
[platform and processor pricing](https://documentation.opencollective.com/why-open-collective/pricing),
and [host eligibility](https://docs.oscollective.org/interested-in-joining-osc/acceptance-criteria).

Ko-fi currently supports one active goal per page. That can support general project funding,
as linked from this site, but it does not provide the proposed several simultaneous model pots.
See [Ko-fi goals](https://help.ko-fi.com/hc/en-us/articles/360004392158-Set-your-Ko-fi-Goal).

## Required funding records

A future implementation needs an eligible payment provider or fiscal host and a stable ID for
each model pot. Payment, refund, and dispute records must update that pot's public total
automatically and idempotently. Show the exact model configuration, amount raised, target,
status, and eventual result link. Close funding when its target is reached and retain an
auditable record of any excess contribution.

If a custom service is needed, keep it separate from the static benchmark publication. GitHub
is not the payment ledger. Provider credentials and webhook secrets stay server-side; expose
only aggregate funding data. Supporter attribution requires explicit consent, and customer
records, email addresses, invoices, payment IDs, tokens, and webhook payloads remain private.

## Proposed money rules

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

- The selected provider/host permits this activity and accepts the project.
- Multiple supporters can contribute different amounts to the same model pot.
- Payments cannot be attributed to the wrong funding pot.
- Paid, refunded, and disputed webhook events update totals idempotently.
- The public total reconciles with the payment ledger while excluding taxes and clearly defining
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
