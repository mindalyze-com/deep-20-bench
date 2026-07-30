# Source layout

Deep20Bench source code is grouped by responsibility.

```text
source/
├── execution/
│   ├── oracle/       Oracle, Reviewer, and Judge
│   ├── game/         one-game engine and Guesser integration
│   └── benchmark/    benchmark control plane
└── publication/
    ├── compiler/     deterministic Python publication compiler
    └── site/         Vue and Vite website
```

Execution code may not depend on publication code or generated publication data. Publication
reads completed artifacts from `runs/` only after model execution. Moving source code does not
change the Guesser-visible protocol or artifact layout.
