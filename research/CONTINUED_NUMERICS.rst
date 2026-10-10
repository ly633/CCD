Numerical arguments for the 80 percent research phase
====================================================

C03: exact dyadic reciprocal multiplication
------------------------------------------

The internal denominators originate in NumCCD.denominator() and are exactly
2^n for 0 <= n < 63. Both d and r=1/d=2^-n are exactly representable normal
doubles. For a stored rounded intermediate x, the exact real quantities x/d
and x*r are equal; correctly rounded IEEE division and multiplication
therefore return the same double (including gradual underflow and signed
zero). Crucially, the preceding multiplication x=fl(delta*numerator) remains
separate; delta*(numerator/d) would not have this property and is not used.
No FMA contraction or reassociation is enabled. The original error bound,
corner order, and every root-finder decision are preserved. The generic
public array evaluator is unchanged; this specialization is only used with
the dyadic arrays produced by convert_tuv_to_array. As in earlier proofs,
the original supported-input and fixed FP environment assumptions apply.

C04: reuse repeated spatial interpolations
-----------------------------------------

For each fixed t, the two u values repeat across v and the two v values
repeat across u. Cache those identical rounded spatial subexpressions.
EE combines the same four (u,v) pairs by subtraction; VF keeps the original
(u_term + v_term) + b parentheses before subtraction from a. Operand order,
rounded intermediate values and output corner order are unchanged; added
rounding error is zero relative to C03 and thus to the original evaluator.

C05: materialize initial-box dyadic arrays directly
-------------------------------------------------

For [0,1]^3, convert_tuv_to_array always produces the same arrays of zeros
and ones and denominators all equal to one. Materializing those arrays
directly is exact and calls the same dimension evaluator in the same x,y,z
order. Computing true_tol is unnecessary on this precheck because only its
Boolean result is used; removing this unused subtraction does not change
the comparisons. No endpoint interpolation is replaced by an input endpoint.

C06: inline dyadic powers and comparisons
---------------------------------------

Move power() and NumCCD::operator< into the header as inline definitions,
retaining the same integer shifts, unsigned multiplications, branches and
assertions. They compute exactly the same integer comparison. This changes
call overhead only; it does not convert comparisons to approximate doubles
or change the priority-queue comparator/order.

C07: exact swept AABB rejection, minimum_separation=0 only
--------------------------------------------------------

For t in [0,1], each coordinate of p(t)=(1-t)p0+t*p1 lies in the closed
interval [min(p0,p1),max(p0,p1)]. A segment/triangle point is a convex
combination of its moving vertices and therefore stays in the coordinate
hull of all its endpoint vertices. Strict separation of either coordinate
interval is a necessary-condition failure for any collision, including
endpoint and grazing contact (equal bounds are NOT rejected).

The hull uses only min/max selections and strict comparisons of finite input
doubles, not subtractions, interpolations, or rounded differences. Its added
numerical error is zero. A common monotone rational-to-double conversion also
cannot turn overlapping endpoint coordinate intervals into strictly disjoint
ones, so the archive's exact-rational provenance does not invalidate this
necessary condition. The test is only enabled for BFS with ms=0 and valid
t_max in [0,1]; the full [0,1] hull is conservative when t_max<1.

Rejected queries provably have no collision and return toi=infinity and the
input tolerance. All surviving queries use the unchanged solver and retain
its exact TOI and conservative error bounds. This can remove original false
positives and is allowed by the user's FP ceilings. The evaluator records
all bitwise mismatches, classifies only old ground-truth-negative hits that
become no-hit with infinity/input tolerance as permitted removals, and rejects
EVERY other mismatch (including changed TOI of retained hits). FN must remain
zero and per-group FP cannot increase. This stronger-than-required retained
TOI check is not silently disabled to accept Boolean-only results.

C08: outward-rounded Bernstein coplanarity certificate
------------------------------------------------------

A VF or EE collision requires the four vertices to be coplanar. Define the
three relative linear trajectories r=a-d, s=b-d, q=c-d. By multilinearity,
their determinant on [0,1] is

  (1-t)^3 D000 + t(1-t)^2 (D100+D010+D001)
  + t^2(1-t) (D011+D101+D110) + t^3 D111,

where Dijk=det(r_i,s_j,q_k). Every scalar basis factor is nonnegative.
If all four displayed coefficient groups have the same strict sign, the
determinant is strictly nonzero for every t, including endpoints, so there
is no collision. Division of middle Bernstein coefficients by three is
unnecessary for a sign test.

Every input coordinate is first enclosed by its two adjacent doubles. This
contains both the exact supplied double and its source rational under the
pinned reader's correctly truncated conversion. Interval add/subtract use
nextafter toward -infinity on the lower result and +infinity on the upper
result. Multiplication uses all four endpoint products followed by the same
outward expansion. Correctly rounded arithmetic is at most one adjacent
representable value from the exact result, including subnormal underflow,
so each operation encloses its exact interval image. Induction through the
determinants and sums gives rigorous coefficient enclosures, not empirical
epsilon choices. Dependency overestimation can only make the test inconclusive.

The filter falls back without rejecting unless every input is finite with
absolute value <=1e90. All intermediate interval magnitudes are then bounded
by a small constant times 1e270, far below double overflow. No fast-math or
FMA contraction is introduced. It is enabled only for double, BFS, ms=0,
after the original initial-box test has accepted. Strict signs exclude zero;
uncertain or zero-containing bounds fall through to the original algorithm.
All surviving collision times would be computed by the unchanged solver.
Tests for known interior/endpoint contacts across 1000 binary scales were
added, alongside the existing corner-equivalence checks. These C08 tests
and its fixed-subset evaluation have NOT executed: Windows rejected process
creation with WinError 4551. The argument above is an implementation rationale,
not a claim that C08 has passed empirical validation or is the delivered best.

Recovery and C09: delay the same certificate until BFS refinement 32
-------------------------------------------------------------------

On the resumed run, system policy state was 0 and the identical C08 files
executed successfully: focused tests and fixed-subset validation passed.
The earlier blocked-test paragraphs above describe the historical state.
C09 moves the same whole-[0,1] geometric certificate into BFS at refinement
32. Queries that return earlier keep the original solver outputs. On the
triggered queries the certificate still proves absence of collision over
the entire original time domain, irrespective of the current subinterval;
it cannot remove a true contact or perturb a surviving contact time.
The filter is called at most once per BFS invocation, only when ms=0.
An inconclusive result changes no queue, tolerance, or floating computation
in the original solver. Delaying a sound rejection can retain some original
false positives that C08 removed, but cannot create a new false positive
relative to the unmodified solver. The normal full output gate still applies.

C10: specialize the subdivision callback
---------------------------------------

Replace the local split_and_push std::function parameter with a deduced
callable template. The same captured references are invoked with the same
intervals in the same order. Interval bisection, integer arithmetic, all
floating operations, the queue comparator and tie order are unchanged.
This removes type erasure and indirect calls; the numerical error added
relative to C09 is zero. Both DFS and BFS call sites instantiate the same
unchanged function body with their existing lambdas.

C11: inline exact interval arithmetic on top of C10
-------------------------------------------------

C11 moves the unchanged definitions of reduction, NumCCD addition,
is_sum_leq_1, Interval::bisect, Interval::overlaps and width into the header
as inline functions. Integer operation order, reduction loops, overflow
behavior/assertions and every floating expression are unchanged. No new
approximation or rounding error is introduced; the objective is to expose
small arithmetic to the compiler across translation-unit boundaries.
C10's callback remains in this candidate. Its single-run subset regression
was provisional; C11 tests the combination with inlined interval arithmetic.
The source revision and hashes are authoritative for this dependency.

C12: explicit four-lane AVX2 corner arithmetic
---------------------------------------------

In double AVX2 builds pack independent vertex interpolations and spatial
terms into four lanes. Every lane still performs subtract, multiply by
numerator, multiply by exact reciprocal, and add in that order. VF keeps
(x+y)+b before subtraction from a; EE keeps its separate two interpolated
edge points before subtraction. There are no FMA intrinsics or horizontal
floating reductions. Lane permutations and loads/stores introduce no
rounding. The scalar path remains for other builds. Thus the original
per-corner error bound applies unchanged under the fixed IEEE environment.
The 3.2 million bitwise corner comparisons explicitly exercise this path,
in addition to the fixed dataset and retained-TOI gate.

C13: compact exact dyadic storage from C11
-----------------------------------------

Revert C12's explicit SIMD after its slower screening result. Pack NumCCD
with one-byte member alignment, retaining the full uint64 numerator and
uint8 denominator exponent. No bit is discarded and every operation is
unchanged. NumCCD shrinks from 16 to 9 bytes, Interval3 from 96 to 54 bytes,
and the BFS node from 104 to 60 bytes on the target compiler. Only memory
layout/copy cost changes; there is no numerical approximation. This changes
the public struct ABI and requires recompiling consumers, as done for all
research executables. Unaligned integer loads are supported by the target
x64 machine; performance is measured instead of assumed.
