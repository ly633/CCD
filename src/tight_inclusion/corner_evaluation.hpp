#pragma once

#include <tight_inclusion/types.hpp>
#include <array>
#if defined(__AVX2__)
#include <immintrin.h>
#endif

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
#if defined(__AVX2__) && defined(TIGHT_INCLUSION_WITH_DOUBLE_PRECISION)
        const __m256d p0 = _mm256_setr_pd(a0,b0,c0,d0);
        const __m256d delta = _mm256_sub_pd(_mm256_setr_pd(a1,b1,c1,d1),p0);
        const __m256d inv = _mm256_setr_pd(ui[0],ui[1],vi[0],vi[1]);
        for (int k=0;k<8;k+=4) {
            const Scalar ti = Scalar(1)/t_dw[k];
            const __m256d pt = _mm256_add_pd(_mm256_mul_pd(
                _mm256_mul_pd(delta,_mm256_set1_pd(t_up[k])),_mm256_set1_pd(ti)),p0);
            double p[4]; _mm256_storeu_pd(p,pt);
            const Scalar a=p[0],b=p[1],c=p[2],d=p[3];
            const __m256d num = _mm256_setr_pd(u_up[k],u_up[k+2],v_up[k],v_up[k+1]);
            const __m256d dif = is_vertex_face
                ? _mm256_setr_pd(c-b,c-b,d-b,d-b)
                : _mm256_setr_pd(b-a,b-a,d-c,d-c);
            __m256d xy = _mm256_mul_pd(_mm256_mul_pd(dif,num),inv);
            if constexpr (!is_vertex_face)
                xy = _mm256_add_pd(xy,_mm256_setr_pd(a,a,c,c));
            double q[4]; _mm256_storeu_pd(q,xy);
            const __m256d x=_mm256_setr_pd(q[0],q[0],q[1],q[1]);
            const __m256d y=_mm256_setr_pd(q[2],q[3],q[2],q[3]);
            __m256d value;
            if constexpr (is_vertex_face)
                value=_mm256_sub_pd(_mm256_set1_pd(a),
                    _mm256_add_pd(_mm256_add_pd(x,y),_mm256_set1_pd(b)));
            else value=_mm256_sub_pd(x,y);
            _mm256_storeu_pd(result.data()+k,value);
        }
#else
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
#endif
        return result;
    }
} // namespace ticcd::detail
