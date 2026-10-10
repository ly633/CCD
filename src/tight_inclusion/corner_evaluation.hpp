#pragma once

#include <tight_inclusion/types.hpp>
#include <array>

namespace ticcd::detail {
    // Internal specialization for the exact layout from convert_tuv_to_array:
    // t = 00001111, u = 00110011, v = 01010101.
    // Cache repeated temporal interpolation WITHOUT changing any individual
    // subtract/multiply/divide/add operation or its rounding order. The public
    // function_ee/function_vf accepting arbitrary arrays remain unchanged.
    template <bool is_vertex_face>
    std::array<Scalar, 8> evaluate_corners_tuv(
        const Scalar a0, const Scalar b0, const Scalar c0, const Scalar d0,
        const Scalar a1, const Scalar b1, const Scalar c1, const Scalar d1,
        const std::array<Scalar, 8>& t_up,
        const std::array<Scalar, 8>& t_dw,
        const std::array<Scalar, 8>& u_up,
        const std::array<Scalar, 8>& u_dw,
        const std::array<Scalar, 8>& v_up,
        const std::array<Scalar, 8>& v_dw)
    {
        std::array<Scalar, 8> result;
        // Denominators produced by NumCCD are exact powers of two. Their
        // reciprocals are exact normal doubles, so correctly-rounded x/d
        // and x*(1/d) have identical results, including gradual underflow.
        const Scalar ui[2] = {Scalar(1) / u_dw[0], Scalar(1) / u_dw[2]};
        const Scalar vi[2] = {Scalar(1) / v_dw[0], Scalar(1) / v_dw[1]};
        for (int k = 0; k < 8; k += 4) {
            const Scalar ti = Scalar(1) / t_dw[k];
            const Scalar a = (a1 - a0) * t_up[k] * ti + a0;
            const Scalar b = (b1 - b0) * t_up[k] * ti + b0;
            const Scalar c = (c1 - c0) * t_up[k] * ti + c0;
            const Scalar d = (d1 - d0) * t_up[k] * ti + d0;
            if constexpr (is_vertex_face) {
                const Scalar x0 = (c - b) * u_up[k] * ui[0];
                const Scalar x1 = (c - b) * u_up[k + 2] * ui[1];
                const Scalar y0 = (d - b) * v_up[k] * vi[0];
                const Scalar y1 = (d - b) * v_up[k + 1] * vi[1];
                result[k] = a - (x0 + y0 + b);
                result[k + 1] = a - (x0 + y1 + b);
                result[k + 2] = a - (x1 + y0 + b);
                result[k + 3] = a - (x1 + y1 + b);
            } else {
                const Scalar x0 = (b - a) * u_up[k] * ui[0] + a;
                const Scalar x1 = (b - a) * u_up[k + 2] * ui[1] + a;
                const Scalar y0 = (d - c) * v_up[k] * vi[0] + c;
                const Scalar y1 = (d - c) * v_up[k + 1] * vi[1] + c;
                result[k] = x0 - y0;
                result[k + 1] = x0 - y1;
                result[k + 2] = x1 - y0;
                result[k + 3] = x1 - y1;
            }
        }
        return result;
    }
} // namespace ticcd::detail
