#pragma once
#include <tight_inclusion/types.hpp>
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

namespace ticcd::detail {
    // Outward enclosures; each stored input is expanded by one adjacent
    // double to also enclose the archive's rational-to-double conversion.
    struct FilterInterval { double lo, hi; };
    inline double down(double x) { return std::nextafter(x,-std::numeric_limits<double>::infinity()); }
    inline double up(double x) { return std::nextafter(x,std::numeric_limits<double>::infinity()); }
    inline FilterInterval add(FilterInterval a, FilterInterval b)
    { return {down(a.lo+b.lo),up(a.hi+b.hi)}; }
    inline FilterInterval sub(FilterInterval a, FilterInterval b)
    { return {down(a.lo-b.hi),up(a.hi-b.lo)}; }
    inline FilterInterval mul(FilterInterval a, FilterInterval b)
    {
        const double p=a.lo*b.lo,q=a.lo*b.hi,r=a.hi*b.lo,s=a.hi*b.hi;
        return {down(std::min({p,q,r,s})),up(std::max({p,q,r,s}))};
    }
    using FilterVector=std::array<FilterInterval,3>;
    inline FilterVector difference(const Vector3& a,const Vector3& b)
    {
        FilterVector r;
        for(int k=0;k<3;++k)r[k]=sub({down(a[k]),up(a[k])},{down(b[k]),up(b[k])});
        return r;
    }
    inline FilterInterval determinant(const FilterVector& a,const FilterVector& b,const FilterVector& c)
    {
        return add(sub(mul(a[0],sub(mul(b[1],c[2]),mul(b[2],c[1]))),
                       mul(a[1],sub(mul(b[0],c[2]),mul(b[2],c[0])))),
                       mul(a[2],sub(mul(b[0],c[1]),mul(b[1],c[0]))));
    }
    inline int definite_sign(FilterInterval x)
    { return x.lo>0 ? 1 : (x.hi<0 ? -1 : 0); }
    inline bool bernstein_separated(
        const Vector3& a0,const Vector3& b0,const Vector3& c0,const Vector3& d0,
        const Vector3& a1,const Vector3& b1,const Vector3& c1,const Vector3& d1)
    {
#ifndef TIGHT_INCLUSION_WITH_DOUBLE_PRECISION
        return false;
#else
        // Conservative fallback outside a domain with ample overflow margin.
        for(const Vector3* p:{&a0,&b0,&c0,&d0,&a1,&b1,&c1,&d1})
            for(int k=0;k<3;++k)if(!std::isfinite((*p)[k]) || std::abs((*p)[k])>1e90)return false;
        const auto r0=difference(a0,d0),s0=difference(b0,d0),q0=difference(c0,d0);
        const int sign=definite_sign(determinant(r0,s0,q0));
        if(!sign)return false;
        const auto r1=difference(a1,d1),s1=difference(b1,d1),q1=difference(c1,d1);
        if(definite_sign(determinant(r1,s1,q1))!=sign)return false;
        const auto b1sum=add(add(determinant(r1,s0,q0),determinant(r0,s1,q0)),determinant(r0,s0,q1));
        if(definite_sign(b1sum)!=sign)return false;
        const auto b2sum=add(add(determinant(r0,s1,q1),determinant(r1,s0,q1)),determinant(r1,s1,q0));
        return definite_sign(b2sum)==sign;
#endif
    }
} // namespace ticcd::detail
