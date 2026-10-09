Tight-Inclusion CCD research protocol
====================================

Goal and protection
-------------------

The user raised the target on 2026-10-09. Stop after a >=80% reduction of
median full CCD core time with validation, or 20 evaluated candidates.
C01 and C02 remain preserved and count as the first two experiments; the
continued series starts at C03. The earlier 20% result is historical evidence,
not completion of the new 80% objective. Historical reports are not overwritten.
The sibling Tight-Inclusion worktree and its data/results are read-only inputs.
All changes and new results belong to Tight-Inclusion-autoresearch.
Historical 74.37439 s is context only, never the comparison denominator.

Experiment controls
-------------------

* Windows 11, Intel Core Ultra 7 265KF, MSVC Release /O2 /Ob2 /DNDEBUG,
  /arch:AVX2 in the CCD library, default precise FP (no fast-math).
* One benchmark process at a time, one computation thread, CPU affinity 0;
  OMP/MKL/OpenBLAS threads = 1. Preprocessing may run concurrently on 8 CPUs
  but must finish before timing. No compilation during timed experiments.
* double, BFS, tolerance=1e-6, max_iterations=1000000,
  minimum_separation=0, t_max=1, err=(-1,-1,-1), no_zero_toi=false.
* All 59,387,883 source queries are parsed by the exact pinned upstream
  CCD-Query-IO reader, which uses GMP rational conversion. Cache records
  contain the resulting 24 doubles and the ground-truth flag verbatim.
  Every source CSV SHA256 is checked against the extraction manifest.
  Cache SHA256 manifests and exact record counts are retained.
* Full group counts: 17,959,962 / 41,372,584 / 21,208 / 34,129.
  In order: simulation VF, simulation EE, handcrafted VF, handcrafted EE.
  FN=0 for each group. FP ceilings=2 / 17 / 90 / 203.
* The same harness and cache order serve an unmodified upstream v1.0.6
  library and each candidate. Timing uses the upstream per-query Timer,
  starting before API argument conversion and stopping after the CCD call.
  CSV/cache I/O, correctness checks, hashes and output writing are outside
  timing. Wall time is recorded separately and is not an optimization result.
* Every answer stores bool, TOI, and output_tolerance, including infinity
  for no-hit. By default candidates must match reference answers bit for bit.
  Starting with C07, an explicit --allow-fp-removal gate permits ONLY an old
  ground-truth-negative hit to become no-hit with infinity and input tolerance.
  Every other mismatch is rejected, including changed TOI of retained hits.
  A new geometric filter also requires an analytical conservativeness proof;
  the dataset's zero-FN result alone is insufficient. This exception implements
  the user's permission to reduce FP, without relaxing retained TOI accuracy.

Screening and final comparison
------------------------------

Subset selection was fixed before candidate implementation: sorted source
paths; all handcrafted records; simulation indices 0,128,256,... per CSV and
all ground-truth-positive records, without duplicates.
This emphasizes difficult cases and has a different timing composition from
the full data. Subset improvement alone cannot meet the goal.

First measure unchanged reference and profile with the upstream nested
timers (diagnostic overhead means profile time is not a performance result).
For each candidate retain hypothesis, code patch/snapshot, compiler config,
binary SHA256, parameters, logs, correctness, and accept/reject reasons.
Do not count harness checks or repeated timings as separate candidates.
At final validation alternate reference,candidate at least three times each.
Compare medians of per-run sums of four CCD group times, not wall time or
the sum of independently selected group medians.

Reproduction entry points
-------------------------

From the research worktree::

    python research/research.py init
    cmake -S . -B build-autoresearch-sample -DTIGHT_INCLUSION_RESEARCH=ON
    cmake --build build-autoresearch-sample --config Release --target research_reference research_profile research_candidate --parallel 8
    python research/research.py prepare --workers 8
    python research/research.py run --id ref-subset --kind reference --hypothesis "Fixed subset reference" --repeats 2
    python research/research.py run --id profile-subset --kind profile --hypothesis "Locate predicate cost; instrumented diagnostic only" --expected research-results/runs/ref-subset

Use new experiment IDs for reruns; existing results/cache are not overwritten.
The baseline run-baseline.py guard remains intact. All reference source files
are extracted from git tag v1.0.6 into research/reference by init; they are
not candidate edits and can always be reconstructed from git.

Limitations
-----------

The archive supplies Boolean ground truth rather than exact contact times.
Bitwise TOI equivalence establishes preservation of the original behavior,
not an independent proof of the original algorithm's absolute TOI accuracy.
The archive counts differ from the paper's tables; this is the full published
archive, not a claim of exact reproduction of every number in the paper.
