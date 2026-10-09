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
