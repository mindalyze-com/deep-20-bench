# Guesser output-contract recovery and reliability

## Protocol rule

Game-policy version 9 retains the scored way for the model under test to recover from an output that
fails the public structured-action contract. There is no invisible Guesser output
retry. Version 9 extends the labelled, bounded stable-knowledge fallback to the Reviewer; that
adjudication change does not alter the Guesser output wire format or visible information
boundary.

The provider wire response must match exactly one of these branches:

```json
{
  "result": {
    "action": "ASK",
    "question": "Was the person born before 1900?",
    "name": null,
    "description": null
  }
}
```

```json
{
  "result": {
    "action": "GUESS",
    "question": null,
    "name": "Albert Einstein",
    "description": "The theoretical physicist associated with relativity."
  }
}
```

The root and action objects reject additional fields. Active strings must be non-empty, and
inactive fields must be JSON `null`.

Concrete contract violations include:

- plain prose such as `I would ask whether the person was born before 1900`;
- invalid or truncated JSON;
- a missing `result` envelope;
- an unsupported action;
- a missing required field or an additional field;
- an inactive field containing an empty string instead of `null`.

These examples classify shape only. The benchmark never sends the concrete malformed response
back to the model.

A Guesser provider call that ends without a completed structured action is classified the same
way and attributed to the model under test, not to infrastructure:

- `output_limit_exceeded`: the model consumed its whole configured output ceiling
  (finish reason `length`) before completing the action;
- `empty_output`: the provider returned a completed choice with no textual structured output;
- `incomplete_output`: the provider returned a choice with another non-`stop` finish reason.

A Guesser `length` finish is never blindly re-sent: an identical request would
deterministically burn the same output budget again, so the call fails fast into the scored
recovery below. Empty and incomplete responses keep their single transient retry before they
are classified. Oracle, Reviewer, Judge, and Guess Validator calls keep their infrastructure
attribution and recovery behavior.

## Scored recovery

Before the question limit, an invalid output:

1. is recorded as a typed `contract_violation` turn;
2. consumes one counted turn;
3. is not sent to the Oracle, Reviewer, Judge, or Guess Validator;
4. receives the one canonical `FORMAT_ERROR` user event; and
5. continues with the model's next turn and next subject-independent sampling seed.

The fixed event says only that the preceding response broke the structured-action contract,
consumed one counted turn, and was not semantically checked. It displays the two public wire
formats and asks the model to try again. It never says whether the attempted question or guess
was correct.

On the final guess-only opportunity, an invalid output is still recorded as a contract
violation but terminates as the scoring-eligible `invalid_guesser_output` model failure. No
second correction is sent and no count beyond the already exhausted limit is added.

Every repeated violation is handled independently. A model can therefore recover and later
identify the subject, but it has lost one counted turn for each pre-limit violation.

Repeated violations are bounded. After `max_consecutive_contract_violations` counted
violations in a row (policy default 5), the episode terminates as the scoring-eligible
`consecutive_contract_violations_exhausted` model failure instead of consuming the remaining
question budget. Any valid structured action resets the consecutive counter.

## Isolation review

`FORMAT_ERROR` is the only new Guesser-visible input. It is canonical, versioned,
subject-independent, and identical across targets, models, providers, and parser failures. The
provider schema and the event's concrete `required_formats` are both rendered from the same
canonical action-contract definitions in
`source/execution/game/src/deep20_game/models.py`; the recovery event
does not carry a separately maintained copy of the wire format.

The following data is never placed in the next Guesser request:

- the malformed output itself;
- JSON-parser or schema-validation details;
- the report-only violation-kind classification (`invalid_json`, `invalid_action`,
  `output_limit_exceeded`, `empty_output`, `incomplete_output`);
- Oracle, Reviewer, Judge, or Guess Validator input, output, evidence, decision, disagreement
  state, or explanation;
- subject identity or private state;
- provider traces, costs, latency, cache telemetry, call IDs, or logs.

The invalid response is absent from Guesser-visible history. Only the fixed `FORMAT_ERROR`
event is appended. Durable post-call artifacts may retain typed report classifications, and
standalone verbose audits may retain provider material, but neither may be reused as model
context.

## Reliability reporting

Gameplay outcome and output-contract reliability are separate aspects. Every episode, subject,
run, leaderboard row, Markdown report, and public web report carries:

- `evaluated_outputs`;
- `valid_outputs`;
- `violations`;
- `counted_penalties`;
- `affected_trials`;
- `compliance_rate = valid_outputs / evaluated_outputs`; and
- status `clean`, `breached`, or `not_evaluable`.

A successful 30-question episode with one earlier format failure remains successful, and its
counted-question total already includes the lost turn. It is also permanently labeled
`breached` with one violation. Reliability does not add a second score penalty; it exposes that
the model was operationally unreliable.

The contract is short, explicit, and fixed for the whole episode. Compliance therefore tests
whether the model can retain and apply a clear instruction as the conversation grows. A
violation can show that the model lost track of the required action format, returned an invalid
or incomplete action, or stopped before completing one. This is distinct from gameplay
accuracy: a model can identify the subject and still break the protocol, or fail to identify it
while following the protocol correctly.

The episode transcript contains a distinct violation card in the exact turn position. Reports
use the explicit wording “Model broke the output contract” for breached trials.

An explicit post-run capture reads signed owner-only `error-outputs.jsonl` files and writes a
tracked, public-safe Guesser-violation snapshot. It keeps only turn identity, violation kind,
attempt number, finish reason, and exact visible Guesser text. It drops call IDs, response IDs,
recovery metadata, and every support-model record. The publication compiler reads this snapshot,
not the owner-only diagnostics. The snapshot and public report are never model or cache input.

## Caching and versions

The fixed correction forms a deterministic appended prompt tail. It can reuse an unchanged
provider prompt prefix, but it cannot reuse an earlier response. Application response caching
and OpenRouter response caching remain prohibited.

This is a clean artifact-contract break with no legacy loader:

- game policy: version 9;
- Guesser prompt: `stateful-category-guesser-v10-unknown-evidence-guidance`;
- Guesser output schema: `guesser_action_v3`;
- episode result: schema version 9;
- benchmark summary/result/manifest: schema version 3; and
- active protocol-9 public dataset: schema version 7.

The independent publisher is pinned to protocol 9 and rejects older episode artifacts.

Old benchmark artifacts must be deleted or kept outside the current publication input. They
are not migrated or inferred. Runtime models reject retired policy, catalog, call-record, and
configuration versions rather than normalizing them.
