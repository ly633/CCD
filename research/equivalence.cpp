#include <tight_inclusion/avx.hpp>
#include <tight_inclusion/corner_evaluation.hpp>
#include <tight_inclusion/bernstein_filter.hpp>
#include <tight_inclusion/projection_filter.hpp>
#include <random>
#include <cstring>
#include <iostream>
#include <cmath>
using namespace ticcd;
namespace ticcd { int find_next_split(const Array3&,const Array3&); }
int main() {
    const Vector3 b(0,0,0),c(1,0,0),d(0,1,0);
    for(int k=0;k<1000;++k) {
        const double h=std::ldexp(1.,-k);
        const Vector3 a0(.25,.25,h),a1(.25,.25,-h),touch(.25,.25,0);
        // Known collisions at interior t=1/2 and at either endpoint.
        if(detail::bernstein_separated(a0,b,c,d,a1,b,c,d) ||
           detail::bernstein_separated(touch,b,c,d,a0,b,c,d) ||
           detail::bernstein_separated(a0,b,c,d,touch,b,c,d)) {
            std::cerr<<"Bernstein rejected a known contact, exponent "<<k<<"\n";return 1;
        }
        if(detail::swept_hulls_separated<true>(a0,b,c,d,a1,b,c,d) ||
           detail::swept_hulls_separated<true>(touch,b,c,d,a0,b,c,d) ||
           detail::swept_hulls_separated<false>(b,c,Vector3(.5,-h,0),Vector3(.5,h,0),
                                                        b,c,Vector3(.5,-h,0),Vector3(.5,h,0))) {
            std::cerr<<"Projection rejected a known contact, exponent "<<k<<"\n";return 1;
        }
    }
    const Vector3 separated(.25,.25,.5);
    const Vector3 outside(.75,.75,0);
    if(!detail::swept_hulls_separated<true>(outside,b,c,d,outside,b,c,d)) {
        std::cerr<<"Projection failed coplanar separated certificate\n";return 1;
    }
    if(!detail::bernstein_separated(separated,b,c,d,separated,b,c,d)) {
        std::cerr<<"Bernstein failed simple separated certificate\n";return 1;
    }
    std::mt19937_64 rng(0xCCD20261009ULL);
    for(int n=0;n<100000;++n) {
        Array3 widths,tols;
        for(int i=0;i<3;++i) {
            widths[i]=std::ldexp(1.,-int(rng()%63));
            tols[i]=n%11==0 ? 0. : (n%13==0 ? std::numeric_limits<double>::infinity() : std::ldexp(1.,-int(rng()%63)));
        }
        const Array3 ratios=(widths>tols).select(widths/tols,-std::numeric_limits<double>::infinity());
        int expected;ratios.maxCoeff(&expected);
        if(find_next_split(widths,tols)!=expected) {std::cerr<<"Split dimension mismatch\n";return 1;}
    }
    uint64_t checks=0;
    for(int n=0;n<200000;++n) {
        Interval3 itv;
        for(auto& x:itv) {
            uint8_t power=uint8_t(rng()%62);
            uint64_t denom=uint64_t(1)<<power, k=rng()%denom;
            x=Interval(NumCCD(k,power),NumCCD(k+1,power));
        }
        std::array<Scalar,8> t,td,u,ud,v,vd;
        convert_tuv_to_array(itv,t,td,u,ud,v,vd);
        double p[8];
        for(auto& x:p) {
            // Includes cancellation, signed zeros, subnormals and large values.
            x=std::ldexp(double(int64_t(rng()%2000001)-1000000)/1000000.,int(rng()%2075)-1074);
            if(n%17==0) x=std::copysign(0.,x);
        }
        auto a=function_ee(p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],t,td,u,ud,v,vd);
        auto b=detail::evaluate_corners_tuv<false>(p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],t,td,u,ud,v,vd);
        auto c=function_vf(p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],t,td,u,ud,v,vd);
        auto d=detail::evaluate_corners_tuv<true>(p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],t,td,u,ud,v,vd);
        for(int i=0;i<8;++i) {
            if(std::memcmp(&a[i],&b[i],8)||std::memcmp(&c[i],&d[i],8)) {
                std::cerr<<"mismatch case "<<n<<" lane "<<i<<"\n"; return 1;
            }
            checks+=2;
        }
    }
    std::cout<<"PASS "<<checks<<" bitwise scalar corner comparisons (seed 0xCCD20261009)\n";
}
