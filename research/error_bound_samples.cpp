#include <tight_inclusion/interval_root_finder.hpp>
#include <random>
#include <iostream>
#include <iomanip>
#include <cmath>
using namespace ticcd;
int main() {
    std::mt19937_64 rng(0xE220261010ULL);
    for(int i=0;i<4096;++i) {
        double d=std::ldexp(double(rng()>>11)*0x1p-53,-int(rng()%1075));
        if(i==0)d=0;
        if(i==1)d=1;
        if(i==2)d=std::numeric_limits<double>::denorm_min();
        if(i==3)d=std::nextafter(1.,0.);
        const Vector3 v=Vector3::Constant(d);
        const std::array<const Vector3*,8> points{&v,&v,&v,&v,&v,&v,&v,&v};
        std::cout<<std::hexfloat<<d;
        for(bool ms:{false,true}) for(bool vf:{false,true})
            std::cout<<" "<<get_numerical_error(points,vf,ms)[0];
        std::cout<<"\n";
    }
}
