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
