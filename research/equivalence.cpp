#include <tight_inclusion/avx.hpp>
#include <tight_inclusion/corner_evaluation.hpp>
#include <random>
#include <cstring>
#include <iostream>
#include <cmath>
using namespace ticcd;
int main() {
    std::mt19937_64 rng(0xCCD20261009ULL);
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
