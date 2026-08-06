# Question-score confidence intervals

The publication reports a 95% confidence interval beside each official question score. It
estimates repeated-trial uncertainty on the fixed benchmark subjects. It does not estimate
performance on new subjects.

## Statistical unit

Every scored subject trial is an individual experiment. Trials use isolated game state and a
trial-specific sampling condition. The calculation treats trials within a subject as independent
repetitions. This is a modeling assumption. Distinct variation tokens and separate model calls
make the assumption reasonable, but a different seed does not by itself prove statistical
independence. Subjects remain separate strata because their difficulty distributions differ.

For subject `j`, let:

- `n_j` be the number of completed trials;
- `x̄_j` be the average penalized question score;
- `s_j²` be the sample variance of its penalized trial scores;
- `J` be the number of equally weighted subjects.

The published score is:

```text
score = sum(x̄_j) / J
```

The estimated variance and standard error are:

```text
estimated variance = sum(s_j² / n_j) / J²
standard error = sqrt(estimated variance)
```

The interval is:

```text
score ± t(0.975, degrees of freedom) × standard error
```

The degrees of freedom use the Welch–Satterthwaite formula. This gives an approximate t interval
and allows each subject to have a different trial variance. A failed model trial keeps its normal
score penalty of `Q + 1`, so failures contribute to both the score and its repeated-trial
uncertainty. Infrastructure failures remain unscored and prevent an incomplete run from entering
the official cohort.

## Worked example: gpt-oss-120B

The current official run has seven subjects and five trials per subject. Its penalized trial
scores produce these intermediate values:

| Subject | Trial scores | Subject mean | Sample variance |
| --- | --- | ---: | ---: |
| T-0001 | 5, 6, 4, 6, 6 | 5.4 | 0.8 |
| T-0002 | 17, 38, 17, 51, 11 | 26.8 | 288.2 |
| T-0003 | 10, 12, 12, 15, 11 | 12.0 | 3.5 |
| T-0004 | 8, 19, 6, 51, 15 | 19.8 | 331.7 |
| T-0005 | 6, 8, 7, 28, 8 | 11.4 | 86.8 |
| T-0006 | 13, 24, 11, 22, 16 | 17.2 | 31.7 |
| T-0007 | 3, 2, 4, 2, 3 | 2.8 | 0.7 |

The steps are:

1. Average the seven subject means: `13.6286` questions.
2. Calculate `sum(s_j² / 5) / 7²`: `3.0342857`.
3. Take its square root: standard error `1.7419201`.
4. Apply Welch–Satterthwaite: `10.9632` degrees of freedom.
5. Use the two-sided 95% t critical value `2.2018879`.
6. Calculate the margin: `2.2018879 × 1.7419201 = 3.8355129`.
7. Report `13.6286 ± 3.8355`, or `9.7931–17.4641` questions.

The two penalized scores of `51` are part of both the mean and variance. They are a main reason
this model's interval is wide.

## Stability ranking

Every published interval uses the same 95% confidence level, so confidence level cannot rank the
models. The Stability result view ranks the interval width instead:

```text
repeatability measure = upper 95% bound - lower 95% bound
```

The view sorts exact widths from smallest to largest. A smaller width means the aggregate score
was more repeatable across the current seeded trials. The rank does not use the score itself. A model can
therefore rank well for stability while consistently producing a poor question score.

The two-dimensional chart places confidence-interval width on the horizontal axis and question
score on the vertical axis. Lower-left means a model has both a lower score and a smaller
interval width. This chart shows the trade-off but does not create or change a rank.

The main question-score chart includes a companion plot for interval width. Each dot shows the
exact width on a scale that starts at zero. Three background bands divide that displayed scale
into equal numeric ranges. The matching line and dot colors make tighter, middle, and wider
intervals easier to scan. The bands are presentation-only and are not fixed quality thresholds.
The scale expands when a wider displayed interval requires it. Equal widths always share a band.
A single valid width or a set of equal widths remains ungrouped.

For gpt-oss-120B, the width is `17.4641 - 9.7931 = 7.6710` questions. For Claude
Opus 5, it is `13.2729 - 11.4128 = 1.8601` questions. Opus is more repeatable in this result set.

## Interpretation

A wider interval means the model produced less consistent trial scores on the current subjects.
All official models use the same subject and trial counts, so interval widths can be compared as
a repeatability signal. It is still an interval for the mean score, not a range expected to
contain individual trial results.

The interval does not include uncertainty from:

- selecting a different subject set;
- changing a model, provider route, prompt, or benchmark version;
- future provider or adjudicator behavior;
- comparing two models directly.

Individual intervals are marginal intervals. Their overlap is not a pairwise significance test.
A direct model comparison should use paired differences for matching subject and trial numbers.

## Publication boundary

The compiler calculates the interval after a run is complete from typed public trial outcomes.
It never writes the interval into a Guesser request, message history, seed, session, cache input,
adjudication request, retry, or later trial. It is reporting-only.
