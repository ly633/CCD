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
        for (int k = 0; k < 8; k += 4) {
            const Scalar a = (a1 - a0) * t_up[k] / t_dw[k] + a0;
            const Scalar b = (b1 - b0) * t_up[k] / t_dw[k] + b0;
            const Scalar c = (c1 - c0) * t_up[k] / t_dw[k] + c0;
            const Scalar d = (d1 - d0) * t_up[k] / t_dw[k] + d0;
            for (int j = 0; j < 4; ++j) {
                const int i = k + j;
                if constexpr (is_vertex_face) {
                    const Scalar pt = (c - b) * u_up[i] / u_dw[i]
                                      + (d - b) * v_up[i] / v_dw[i] + b;
                    result[i] = a - pt;
                } else {
                    const Scalar va = (b - a) * u_up[i] / u_dw[i] + a;
                    const Scalar vb = (d - c) * v_up[i] / v_dw[i] + c;
                    result[i] = va - vb;
                }
            }
        }
        return result;
    }
} // namespace ticcd::detail
