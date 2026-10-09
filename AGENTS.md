# CCD research worktree

This checkout is `D:/ly/DGP-Autoreasearch/Tight-Inclusion-autoresearch`, on
`research/ccd-autoresearch`, created from the verified baseline commit
`497baaab37b9a080d8d0db5b84ea13f50fc507e0`.

Make research changes and save new experiment outputs in this worktree.
The sibling `../Tight-Inclusion` checkout holds the baseline branch and the
downloaded datasets. Treat its source, build products, results, and datasets
as reference inputs; do not modify them as part of research experiments.
This is a standard Git linked worktree, sharing Git history with the baseline.

Read `AUTORESEARCH.rst` for local paths, build commands, and the baseline
metrics. Follow the user's latest concrete research goal, constraints, and
stopping conditions. Worktree preparation by itself does not start Goal Mode.

For experiments, record the hypothesis, source revision/diff, dataset hash,
parameters, build flags, timing scope, and correctness results. Preserve failed
experiments as evidence. Compare candidates with the original baseline using
the same data and settings; distinguish CCD time from data loading/parsing.

`scripts/run-baseline.py` intentionally rejects modified upstream core code.
When an optimization goal is given, establish an explicit candidate evaluator
that records the source changes and checks correctness, rather than presenting
a modified algorithm as the unchanged baseline.

The complete published archive has 59,387,883 queries. Its handcrafted query
counts differ from the paper's Table 1; do not describe the baseline as an
exact reproduction of every number in the paper. No exact TOI-error measurement
has been performed yet.
