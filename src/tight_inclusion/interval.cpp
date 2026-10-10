// An interval object.
#include "interval.hpp"

#include <cassert>

namespace ticcd {

    static constexpr uint8_t MAX_DENOM_POWER = 8 * sizeof(uint64_t) - 1;

    // return power t. n=result*2^t


    NumCCD::NumCCD(Scalar x)
    {
        // Use bisection to find an upper bound of x.
        assert(x >= 0 && x <= 1);
        NumCCD low(0, 0), high(1, 0), mid;

        // Hard code these cases for better accuracy.
        if (x == 0) {
            *this = low;
            return;
        } else if (x == 1) {
            *this = high;
            return;
        }

        do {
            mid = low + high;
            mid.denom_power++;

            if (mid.denom_power >= MAX_DENOM_POWER) {
                break;
            }

            if (x > mid) {
                low = mid;
            } else if (x < mid) {
                high = mid;
            } else {
                break;
            }
        } while (mid.denom_power < MAX_DENOM_POWER);
        *this = high;
        assert(x <= value());
    }











} // namespace ticcd
