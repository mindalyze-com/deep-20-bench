# Deep20Bench game engine

The `deep20-game` package runs one Twenty Questions episode. It coordinates the model under test
(the Guesser), the quality-controlled live-web Oracle/Reviewer/Judge pipeline, and the
independent no-web Guess Validator under a versioned game policy. As a library it is
filesystem-free and logging-neutral: persistence and execution observation are supplied through
typed protocols.

Start here:

- [Concept](Concept.md) — responsibilities, state transitions, session history, trust
  boundaries, caching, and failure semantics.
- [Usage](Usage.md) — configuration, one-game CLI commands, official cache probes, outputs,
  artifacts, and tests.

The benchmark variable is the Guesser configuration. The Oracle, Reviewer, Judge, and Guess
Validator have independently pinned routes and remain fixed when comparing Guesser models.
Reviewer and Judge settings are nested under the Oracle configuration because the three roles
form one factual-adjudication component.
`deep20-benchmark` invokes this one-episode engine repeatedly and owns scheduling, durable
artifacts, live state, logging, aggregation, and reports. The standalone `deep20 game play`
command remains a command-level composition root for individual development episodes.
