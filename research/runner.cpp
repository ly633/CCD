// Identical evaluator for reference/candidate; only the linked CCD library differs.
#include <tight_inclusion/ccd.hpp>
#include <tight_inclusion/interval_root_finder.hpp>
#include <tight_inclusion/timer.hpp>
#include <tight_inclusion/logger.hpp>
#include <ccd_io/read_ccd_queries.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <cstring>
#include <vector>
#include <chrono>
#include <stdexcept>
#include <cfenv>
#include <xmmintrin.h>
namespace fs = std::filesystem;
using namespace ticcd;
// No padding or uninitialized bytes in portable on-this-machine cache/output.
struct Record { double v[24]; uint64_t truth; };
struct Answer { double toi, tolerance; uint64_t hit; };
static_assert(sizeof(Record)==200 && sizeof(Answer)==24 && sizeof(Scalar)==8);
struct Entry { int group; uint64_t count; std::string path; };
std::vector<Entry> read_list(const fs::path& path) {
    std::ifstream f(path); if (!f) throw std::runtime_error("missing list");
    std::vector<Entry> entries; Entry e;
    while(f >> e.group >> e.count >> e.path) entries.push_back(e);
    if (entries.empty()) throw std::runtime_error("empty list");
    return entries;
}
uint64_t hash_bytes(uint64_t h, const void* p, size_t n) {
    auto b=static_cast<const unsigned char*>(p);
    for(size_t i=0;i<n;++i) h=(h^b[i])*1099511628211ULL;
    return h;
}
int main(int argc,char** argv) try {
    if(argc<5) throw std::runtime_error("pack LIST CSV_ROOT CACHE_ROOT | run LIST CACHE_ROOT ANSWERS_OUT [EXPECTED]");
    logger().set_level(spdlog::level::trace);
    auto entries=read_list(argv[2]);
    if(std::string(argv[1])=="pack") {
        for(const auto& e:entries) {
            auto queries=ccd_io::read_ccd_queries((fs::path(argv[3])/e.path).string());
            if(queries.size()!=e.count) throw std::runtime_error("CSV count mismatch");
            fs::path full=fs::path(argv[4])/"full"/(e.path+".bin");
            fs::path sample=fs::path(argv[4])/"subset"/(e.path+".bin");
            if(fs::exists(full)||fs::exists(sample)) throw std::runtime_error("refusing cache overwrite");
            fs::create_directories(full.parent_path()); fs::create_directories(sample.parent_path());
            std::ofstream a(full,std::ios::binary),b(sample,std::ios::binary);
            uint64_t selected=0;
            for(size_t i=0;i<queries.size();++i) {
                Record r; std::memcpy(r.v,&queries[i].vertices[0][0],192); r.truth=queries[i].ground_truth;
                a.write(reinterpret_cast<const char*>(&r),sizeof(r));
                // Fixed before any candidate: every 128th query per CSV,
                // every true collision, and all handcrafted queries.
                if(e.group>=2 || i%128==0 || r.truth) {b.write(reinterpret_cast<const char*>(&r),sizeof(r)); ++selected;}
            }
            if(!a||!b) throw std::runtime_error("cache write failed");
            std::cout<<"PACK "<<e.group<<" "<<e.path<<" "<<e.count<<" "<<selected<<std::endl;
        }
        return 0;
    }
    if(std::string(argv[1])!="run") throw std::runtime_error("unknown mode");
    const auto mxcsr=_mm_getcsr();
    if((mxcsr & 0xE040) != 0 || std::fegetround()!=FE_TONEAREST)
        throw std::runtime_error("benchmark requires nearest rounding and gradual underflow");
    std::cout << "FP_ENV MXCSR=" << mxcsr << " ROUND=FE_TONEAREST FTZ=0 DAZ=0\n";
    std::ofstream answers(argv[4],std::ios::binary);
    std::ifstream expected;
    if(argc>5) expected.open(argv[5],std::ios::binary);
    if(!answers || (argc>5 && !expected)) throw std::runtime_error("answer file unavailable");
    uint64_t n[4]={},gt[4]={},fp[4]={},fn[4]={},mismatch[4]={},removed_fp[4]={},hash[4];
    for(auto& h:hash) h=14695981039346656037ULL;
    double us[4]={}; Timer timer;
    for(const auto& e:entries) {
        std::vector<Record> records(e.count);
        std::ifstream f(fs::path(argv[3])/e.path,std::ios::binary);
        f.read(reinterpret_cast<char*>(records.data()),e.count*sizeof(Record));
        if(!f || f.peek()!=EOF) throw std::runtime_error("cache size/read mismatch");
        std::vector<Answer> result(e.count),ref(argc>5?e.count:0);
        if(argc>5) {expected.read(reinterpret_cast<char*>(ref.data()),e.count*sizeof(Answer)); if(!expected) throw std::runtime_error("short expected file");}
        for(size_t i=0;i<records.size();++i) {
            const auto& r=records[i];
            using Matrix8x3=Eigen::Matrix<double,8,3,Eigen::RowMajor>;
            Eigen::Map<const Matrix8x3> V(r.v);
            const Array3 err(-1,-1,-1);
            double toi=std::numeric_limits<double>::infinity(),tol=1e-6;
            bool hit;
            timer.start();
            if(e.group%2) {
                hit=edgeEdgeCCD(V.row(0),V.row(1),V.row(2),V.row(3),V.row(4),V.row(5),V.row(6),V.row(7),err,0.,toi,1e-6,1.,1000000,tol,false,CCDRootFindingMethod::BREADTH_FIRST_SEARCH);
            } else {
                hit=vertexFaceCCD(V.row(0),V.row(1),V.row(2),V.row(3),V.row(4),V.row(5),V.row(6),V.row(7),err,0.,toi,1e-6,1.,1000000,tol,false,CCDRootFindingMethod::BREADTH_FIRST_SEARCH);
            }
            timer.stop(); us[e.group]+=timer.getElapsedTimeInMicroSec();
#ifdef RESEARCH_DIAGNOSTIC
            // Diagnostic-only executable: output is outside the measured call.
            // Its timings are never used as optimization results.
            if (timer.getElapsedTimeInMicroSec() > 1000)
                std::cout << std::setprecision(17) << "SLOW " << e.group << " "
                          << e.path << " " << i << " " << r.truth << " " << hit
                          << " " << toi << " " << timer.getElapsedTimeInMicroSec()/1e6 << "\n";
#endif
            result[i]={toi,tol,uint64_t(hit)};
            ++n[e.group]; gt[e.group]+=r.truth;
            fp[e.group]+=hit&&!r.truth; fn[e.group]+=!hit&&r.truth;
            if(argc>5 && std::memcmp(&result[i],&ref[i],sizeof(Answer))) {
                ++mismatch[e.group];
                // Explicitly classify only old false positives becoming
                // no-hit. All other output/TOI changes remain failures.
                if(!r.truth && ref[i].hit && !hit &&
                   toi==std::numeric_limits<double>::infinity() && tol==1e-6)
                    ++removed_fp[e.group];
            }
        }
        hash[e.group]=hash_bytes(hash[e.group],result.data(),result.size()*sizeof(Answer));
        answers.write(reinterpret_cast<const char*>(result.data()),result.size()*sizeof(Answer));
        if(!answers) throw std::runtime_error("answer write failed");
    }
    if(argc>5 && expected.peek()!=EOF) throw std::runtime_error("long expected file");
    for(int g=0;g<4;++g)
        std::cout<<std::setprecision(17)<<"RESULT "<<g<<" "<<n[g]<<" "<<gt[g]<<" "<<fp[g]<<" "<<fn[g]<<" "<<us[g]/1e6<<" "<<mismatch[g]<<" "<<hash[g]<<std::endl;
    for(int g=0;g<4;++g) std::cout<<"REMOVED_FP "<<g<<" "<<removed_fp[g]<<std::endl;
#ifdef RESEARCH_PROFILE
    print_times();
#endif
    return 0;
} catch(const std::exception& e) {std::cerr<<"ERROR "<<e.what()<<std::endl;return 1;}
