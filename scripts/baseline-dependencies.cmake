# Add build-only dependency wiring without editing the upstream CCD sources.
# Use the already installed, exact Eigen version required by the paper code.
find_package(Eigen3 3.4.0 EXACT REQUIRED NO_MODULE)

# setup-baseline.ps1 has fetched the exact data revision used by CCD-Query-IO.
# Defining its expected targets skips ExternalProject's unbounded full clone.
if(NOT EXISTS "${CCD_IO_SAMPLE_QUERIES_DIR}/unit-tests")
    message(FATAL_ERROR "Pinned sample data is missing; run scripts/setup-baseline.ps1")
endif()
add_library(baseline_sample_queries INTERFACE)
add_library(tight_inclusion::sample_queries ALIAS baseline_sample_queries)
add_library(ccd_io::sample_queries ALIAS baseline_sample_queries)
target_compile_definitions(baseline_sample_queries INTERFACE
    CCD_IO_SAMPLE_QUERIES_DIR="${CCD_IO_SAMPLE_QUERIES_DIR}")
