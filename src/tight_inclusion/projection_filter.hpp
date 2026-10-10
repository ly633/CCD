#pragma once
#include <tight_inclusion/bernstein_filter.hpp>
#include <Eigen/Geometry>

namespace ticcd::detail {
    template<bool is_vertex_face>
    bool projection_separated(const std::array<const Vector3*,8>& p,Vector3 axis)
    {
        const double scale=axis.cwiseAbs().maxCoeff();
        if (!(scale>0) || !std::isfinite(scale)) return false;
        axis/=scale; // Any finite stored axis is valid; exact normals are unnecessary.
        double alo=std::numeric_limits<double>::infinity(),ahi=-alo,blo=alo,bhi=-alo;
        for(int i=0;i<8;++i) {
            FilterInterval value{0,0};
            for(int k=0;k<3;++k)
                value=add(value,mul({down((*p[i])[k]),up((*p[i])[k])},{axis[k],axis[k]}));
            const bool first=is_vertex_face ? (i%4==0) : (i%4<2);
            if(first) { alo=std::min(alo,value.lo); ahi=std::max(ahi,value.hi); }
            else { blo=std::min(blo,value.lo); bhi=std::max(bhi,value.hi); }
        }
        return ahi<blo || bhi<alo;
    }

    template<bool is_vertex_face>
    bool swept_hulls_separated(
        const Vector3& a0,const Vector3& b0,const Vector3& c0,const Vector3& d0,
        const Vector3& a1,const Vector3& b1,const Vector3& c1,const Vector3& d1)
    {
#ifndef TIGHT_INCLUSION_WITH_DOUBLE_PRECISION
        return false;
#else
        const std::array<const Vector3*,8> p{&a0,&b0,&c0,&d0,&a1,&b1,&c1,&d1};
        for(const auto* v:p) for(int k=0;k<3;++k)
            if(!std::isfinite((*v)[k]) || std::abs((*v)[k])>1e90) return false;
        for(int t:{0,4}) {
            if constexpr (is_vertex_face) {
                const Vector3 u=*p[t+2]-*p[t+1],v=*p[t+3]-*p[t+1];
                const Vector3 normal=u.cross(v);
                for(const Vector3& axis:std::array<Vector3,4>{normal,normal.cross(u),normal.cross(v),normal.cross(v-u)})
                    if(projection_separated<true>(p,axis)) return true;
            } else {
                const Vector3 u=*p[t+1]-*p[t],v=*p[t+3]-*p[t+2],w=*p[t+2]-*p[t];
                for(const Vector3& normal:std::array<Vector3,2>{u.cross(v),u.cross(w)}) {
                    for(const Vector3& axis:std::array<Vector3,3>{normal,normal.cross(u),normal.cross(v)})
                        if(projection_separated<false>(p,axis)) return true;
                }
            }
        }
        return false;
#endif
    }
}
