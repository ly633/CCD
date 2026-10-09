Continuation toward the unchanged 80 percent target
===================================================

Current status
--------------

Seven effective candidates C01--C07 have been evaluated. C07 is the best
fully validated version: three alternating full pairs give 72.726807293 s
reference versus 42.484861801 s candidate, a 41.58294% reduction. The 80%
goal is incomplete and the 20-candidate limit has not been reached.
See RESULTS80.rst and ../research-results/phase80-c07-summary.json.

C06's earlier WinError 4551 was transient: a later retry of the identical
binary at its original saved path succeeded, with Smart App Control still
enabled and without changing any system policy. The successful dataset
run counts as C06, not a second experiment. C07 then ran successfully.

Pending implementation: C08
--------------------------

Source 285bd4095dcdd1b0b5b0b21c292758320b62b280 adds an interval Bernstein
coplanarity certificate. Build succeeded, but Windows Smart App Control
denied its focused-test process three times (WinError 4551; CodeIntegrity
3077/3033/3118). The last unchanged-file retry was after the entire C07
alternating full comparison. C08 has no focused-test or dataset result;
it does not count toward the effective experiment total.

The current source checkout contains C08, not the validated C07. Keep the
two unchanged executables in build-autoresearch-sample/research/Release;
their hashes and attempted logs are in c08-experiment.json. Do not weaken
security policy, replace, rename or relocate these files to evade the block.
After legitimate execution is possible, resume without rebuilding::

    python research/experiment.py --resume --id C08 --parent C07 --allow-fp-removal --hypothesis "Resume exact unchanged C08 binaries after execution restriction resolves"

The resume command verifies both saved executable hashes before running.
If it succeeds, complete focused tests and fixed-subset validation before
acceptance; reject the candidate on any unclassified output difference.

Next hypotheses, not executed candidates
----------------------------------------

* C07's simulation EE time regressed relative to C05 despite its overall win.
  Test placing the EE swept-AABB filter after the cheap original initial-box
  test while retaining the early VF filter. Both rejection certificates and
  surviving solver behavior can remain identical.
* Replace std::function split callbacks with templates, retaining insertion
  order exactly. Move error-bound vertex storage from vector to array while
  retaining the same axis reductions and floating-point expressions.
* If generic pow(delta,3) is expensive, investigate an explicitly upward
  rounded cube bound. Derive its inflation bound and validate retained TOI;
  do not assume arithmetic equivalence.
* Explicit SIMD corner arithmetic without FMA/reassociation; compact interval
  node storage; queue storage reuse with identical heap and tie behavior.
* Interval-certified projection separation on selected finite axes could
  reject disjoint swept convex hulls. Each projection must enclose all endpoint
  vertices with outward rounding. Axis selection may be approximate because
  any rigorously separating finite axis is a valid certificate. Prove and
  test degeneracy/overflow fallbacks before treating this as a candidate.

Read-only diagnostics found almost no exact repeated geometry and only one
shared-start-vertex contact in the subset; those are not promising speedups.
Diagnostics, build successes, failed process creation and repeated timings
are not effective candidate experiments.

Execution recheck: 2026-10-09 15:15 UTC
-------------------------------------

The first goal continuation verified the same binary hashes and retried C08
at its original path. Attempt 4 still failed before process creation with
WinError 4551. New CodeIntegrity events 3077/3033 confirm the same signing
policy block; policy state remains 1 and the executable is unsigned. There
is no live benchmark process to wait on. This is the second consecutive
goal turn with this blocker, not four effective candidate experiments.
Evidence: ../research-results/c08-continuation-1-environment.json and
../research-results/blocker-audit.json. The 80% goal remains incomplete.

Blocked audit: 2026-10-09 15:16 UTC
---------------------------------

Attempt 5 again failed on the unchanged file at its original path. New
CodeIntegrity 3077/3033 events confirm the same policy restriction, and no
benchmark process is running. This is the third consecutive goal turn with
the same blocker. Goal status is now BLOCKED, not complete. The best validated
version remains C07 with 41.58294% reduction; seven candidates are effective.
Further evaluated research requires legitimate executable access to be
restored. No security policy or signing trust was changed. See
../research-results/c08-continuation-2-environment.json and blocker-audit.json.
