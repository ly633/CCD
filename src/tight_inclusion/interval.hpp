// An interval object.
#pragma once

#include <array>
#include <cassert>

#include <Eigen/Core>

#include <tight_inclusion/types.hpp>
#include <tight_inclusion/config.hpp>

namespace ticcd {

    // calculate a*(2^b)
    inline uint64_t power(const uint64_t a, const uint8_t b)
    {
        assert(b < 8 * sizeof(uint64_t) - 1);
        return a << b;
    }

    // calculate 2^exponent
    inline uint64_t pow2(const uint8_t exponent) { return power(1l, exponent); }

    // return power t. n=result*2^t
    uint8_t reduction(const uint64_t n, uint64_t &result);

    //<k,n> pair present a number k/pow(2,n)
    #pragma pack(push, 1)
    struct NumCCD {
        uint64_t numerator;
        uint8_t denom_power;

        NumCCD() {}

        NumCCD(uint64_t p_numerator, uint8_t p_denom_power)
            : numerator(p_numerator), denom_power(p_denom_power)
        {
        }

        NumCCD(Scalar x);

        ~NumCCD() {}

        uint64_t denominator() const { return pow2(denom_power); }

        // convert NumCCD to double number
        Scalar value() const { return Scalar(numerator) / denominator(); }

        operator double() const { return value(); }

        NumCCD operator+(const NumCCD &other) const;

        bool operator==(const NumCCD &other) const
        {
            return numerator == other.numerator
                   && denom_power == other.denom_power;
        }
        bool operator!=(const NumCCD &other) const { return !(*this == other); }
        bool operator<(const NumCCD &other) const
        {
            uint64_t k1 = numerator, k2 = other.numerator;
            if (denom_power < other.denom_power) {
                k1 = pow2(other.denom_power - denom_power) * k1;
            } else if (denom_power > other.denom_power) {
                k2 = pow2(denom_power - other.denom_power) * k2;
            }
            assert((value() < other.value()) == (k1 < k2));
            return k1 < k2;
        }
        bool operator<=(const NumCCD &other) const
        {
            return (*this == other) || (*this < other);
        }
        bool operator>=(const NumCCD &other) const { return !(*this < other); }
        bool operator>(const NumCCD &other) const { return !(*this <= other); }

        bool operator<(const Scalar other) const { return value() < other; }
        bool operator>(const Scalar other) const { return value() > other; }
        bool operator==(const Scalar other) const { return value() == other; }

        static bool is_sum_leq_1(const NumCCD &num1, const NumCCD &num2);
    };

    #pragma pack(pop)
    static_assert(sizeof(NumCCD) == 9, "compact exact dyadic storage");

    // an interval represented by two double numbers
    struct Interval {
        NumCCD lower;
        NumCCD upper;

        Interval() {}

        Interval(const NumCCD &p_lower, const NumCCD &p_upper)
            : lower(p_lower), upper(p_upper)
        {
        }

        ~Interval() {}

        std::pair<Interval, Interval> bisect() const;

        bool overlaps(const Scalar r1, const Scalar r2) const;
    };

    typedef std::array<Interval, 3> Interval3;
    Array3 width(const Interval3 &x);

    inline uint8_t reduction(const uint64_t n, uint64_t &result)
    {
        uint8_t t = 0;
        result = n;
        while (result != 0 && (result & 1) == 0) {
            result >>= 1;
            t++;
        }
        return t;
    }

    inline NumCCD NumCCD::operator+(const NumCCD &other) const
    {
        const uint64_t &k1 = numerator, &k2 = other.numerator;
        const uint8_t &n1 = denom_power, &n2 = other.denom_power;

        NumCCD result;
        if (n1 == n2) {
            result.denom_power = n2 - reduction(k1 + k2, result.numerator);
        } else if (n2 > n1) {
            result.numerator = k1 * pow2(n2 - n1) + k2;
            assert(result.numerator % 2 == 1);
            result.denom_power = n2;
        } else { // n2 < n1
            result.numerator = k1 + k2 * pow2(n1 - n2);
            assert(result.numerator % 2 == 1);
            result.denom_power = n1;
        }
        return result;
    }

    inline bool NumCCD::is_sum_leq_1(const NumCCD &num1, const NumCCD &num2)
    {
        if (num1.denom_power == num2.denom_power) {
            // skip the reduction in num1 + num2
            return num1.numerator + num2.numerator <= num1.denominator();
        }
        NumCCD tmp = num1 + num2;
        return tmp.numerator <= tmp.denominator();
    }

    inline std::pair<Interval, Interval> Interval::bisect() const
    {
        // interval is [k1/pow2(n1), k2/pow2(n2)]
        NumCCD mid = upper + lower;
        mid.denom_power++; // ÷ 2
        assert(mid.value() > lower.value() && mid.value() < upper.value());
        return std::make_pair(Interval(lower, mid), Interval(mid, upper));
    }

    inline bool Interval::overlaps(const Scalar r1, const Scalar r2) const
    {
        return upper.value() >= r1 && lower.value() <= r2;
    }

    inline Array3 width(const Interval3 &x)
    {
        return Array3(
            x[0].upper.value() - x[0].lower.value(),
            x[1].upper.value() - x[1].lower.value(),
            x[2].upper.value() - x[2].lower.value());
    }

} // namespace ticcd
