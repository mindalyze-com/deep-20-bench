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

Execution code must not depend on publication code or generated publication data. Publication
reads finished results from `runs/` after the models have run. Moving source files does not
change what the Guesser sees or how artifacts are laid out.
