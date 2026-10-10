#pragma once
#include <tight_inclusion/bernstein_filter.hpp>
#include <Eigen/Geometry>

namespace ticcd::detail {
    template<bool is_vertex_face>
    unsigned projection_time_mask(const std::array<const Vector3*,8>& p,Vector3 axis,unsigned covered)
    {
        const double scale=axis.cwiseAbs().maxCoeff();
        if (!(scale>0) || !std::isfinite(scale)) return covered;
        axis/=scale;
        FilterInterval projected[8];
        for(int i=0;i<8;++i) {
            projected[i]={0,0};
            for(int k=0;k<3;++k)
                projected[i]=add(projected[i],mul({down((*p[i])[k]),up((*p[i])[k])},{axis[k],axis[k]}));
        }
        for(int bin=0;bin<8;++bin) {
            if(covered&(1u<<bin)) continue;
            double alo=std::numeric_limits<double>::infinity(),ahi=-alo,blo=alo,bhi=-alo;
            for(int endpoint=0;endpoint<2;++endpoint) {
                const double t=(bin+endpoint)*0.125,w=1-t;
                for(int i=0;i<4;++i) {
                    const auto value=add(mul(projected[i],{w,w}),mul(projected[i+4],{t,t}));
                    const bool first=is_vertex_face ? i==0 : i<2;
                    if(first) {alo=std::min(alo,value.lo);ahi=std::max(ahi,value.hi);}
                    else {blo=std::min(blo,value.lo);bhi=std::max(bhi,value.hi);}
                }
            }
            if(ahi<blo || bhi<alo) covered|=(1u<<bin);
        }
        return covered;
    }

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
        const Vector3& a1,const Vector3& b1,const Vector3& c1,const Vector3& d1,
        const bool partition_time=false)
    {
#ifndef TIGHT_INCLUSION_WITH_DOUBLE_PRECISION
        return false;
#else
        const std::array<const Vector3*,8> p{&a0,&b0,&c0,&d0,&a1,&b1,&c1,&d1};
        for(const auto* v:p) for(int k=0;k<3;++k)
            if(!std::isfinite((*v)[k]) || std::abs((*v)[k])>1e90) return false;
        unsigned covered=0;
        auto separated=[&](const Vector3& axis) {
            if(!partition_time) return projection_separated<is_vertex_face>(p,axis);
            covered=projection_time_mask<is_vertex_face>(p,axis,covered);
            return covered==255;
        };
        for(int t:{0,4}) {
            if constexpr (is_vertex_face) {
                const Vector3 u=*p[t+2]-*p[t+1],v=*p[t+3]-*p[t+1];
                const Vector3 normal=u.cross(v);
                for(const Vector3& axis:std::array<Vector3,4>{normal,normal.cross(u),normal.cross(v),normal.cross(v-u)})
                    if(separated(axis)) return true;
            } else {
                const Vector3 u=*p[t+1]-*p[t],v=*p[t+3]-*p[t+2],w=*p[t+2]-*p[t];
                for(const Vector3& normal:std::array<Vector3,2>{u.cross(v),u.cross(w)}) {
                    for(const Vector3& axis:std::array<Vector3,3>{normal,normal.cross(u),normal.cross(v)})
                        if(separated(axis)) return true;
                }
            }
        }
        return false;
#endif
    }
}
