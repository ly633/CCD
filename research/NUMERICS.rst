Numerical preservation argument for candidate C01
================================================

Transformation
--------------

Only the internal corner evaluator is specialized for the array layout
constructed by convert_tuv_to_array. Its time numerator/denominator pair is
identical for lanes 0..3 and identical for lanes 4..7. The generic exported
function_vf and function_ee remain unchanged for arbitrary array callers.

Let fl denote a double operation under the same floating-point environment.
Each original temporal interpolation has the following operation graph::

    q = fl(fl(fl(fl(x1 - x0) * t_numerator) / t_denominator) + x0)

C01 computes q once per group of four equal operands instead of computing
it four times. Each node has identical operands, precision, and operation
order. Reusing its stored double result adds no rounding. In particular it
does NOT replace (x*n)/d by x*(n/d), use reciprocal approximation, contract
multiply-add, or assume interpolation at t=1 equals the original endpoint.
The original rounded interpolation at both endpoints is retained.

The spatial expressions keep the original order exactly::

    EE: ((b-a)*u_n/u_d+a) - ((d-c)*v_n/v_d+c)
    VF: a - (((c-b)*u_n/u_d + (d-b)*v_n/v_d) + b)

All eight output lanes retain their original order. Consequently the min/max
scan, true_tol subtraction, error-box comparisons, subdivision choices,
priority queue operations, iteration limit, early exits, TOI and returned
tolerance see the same inputs. This yields equality by induction over the
root-finder's iteration sequence, under the upstream supported finite-input
and floating-point assumptions. It does not extend the original method's
domain to inputs on which it already overflows or has invalid arithmetic.

Error bounds and conservativeness
--------------------------------

The transformation adds zero rounding error relative to the original
operation graph. Therefore the original inclusion-filter error bounds
continue to apply without inflation or reduction. For double and ms=0,
get_numerical_error uses 6.217248937900877e-15 for EE and
6.661338147750939e-15 for VF, multiplied by the same axis scale cubed as
the original code. Neither those constants nor the scale calculation is
modified. Spatial tolerances, max_iterations fallback, and all conservative
box tests remain unchanged. This is an equivalence argument preserving the
original guarantees and assumptions, not a claim that dataset tests prove
conservativeness for arbitrary real inputs.

Build and validation controls
-----------------------------

Reference and candidate use the same MSVC 19.44 Release settings and default
precise floating point; no fast-math or new contraction flag is enabled.
The focused equivalence test compares each of eight scalar corner outputs
against the unchanged generic routines using fixed-seed dyadic intervals,
cancellation, signed zeros, subnormal numbers, and large magnitudes.
Dataset evaluation separately compares bool, TOI, and output_tolerance
bit for bit for every query; these empirical checks corroborate, rather
than replace, the operation-graph argument.

The data contains no exact ground-truth contact time. Preserving the
original returned TOI exactly establishes no loss of its time accuracy;
it is not an independent absolute TOI-error measurement. The supplied
1e-6 tolerance is the algorithm's distance tolerance, not a new guarantee
of an absolute 1e-6 time error.
