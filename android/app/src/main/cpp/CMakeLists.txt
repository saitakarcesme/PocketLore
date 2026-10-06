cmake_minimum_required(VERSION 3.22)
project(pocketlore_native LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
foreach(flag LLAMA_BUILD_COMMON LLAMA_BUILD_TESTS LLAMA_BUILD_TOOLS LLAMA_BUILD_EXAMPLES LLAMA_BUILD_SERVER LLAMA_BUILD_APP LLAMA_BUILD_UI LLAMA_OPENSSL GGML_NATIVE GGML_OPENMP GGML_CUDA GGML_VULKAN GGML_RPC GGML_BLAS GGML_LLAMAFILE GGML_CPU_KLEIDIAI GGML_AVX GGML_AVX2 GGML_FMA GGML_F16C GGML_BMI2 GGML_SSE42)
    set(${flag} OFF CACHE BOOL "" FORCE)
endforeach()
set(GGML_CPU_ARM_ARCH armv8-a CACHE STRING "" FORCE)
add_subdirectory("${LLAMA_SOURCE}" llama)
add_library(pocketlore SHARED runtime.cpp sparse_link.cpp)
target_link_libraries(pocketlore PRIVATE llama)
target_compile_definitions(pocketlore PRIVATE POCKETLORE_REVISION="${POCKETLORE_REVISION}")

# Memory accounting API belongs to the exact immutable pinned llama.cpp revision.
target_include_directories(pocketlore PRIVATE "${LLAMA_SOURCE}/src")

# NDK r27: align LOAD and RELRO for both 4 KB and 16 KB Android kernels.
target_link_options(pocketlore PRIVATE "-Wl,-z,max-page-size=16384" "-Wl,-z,common-page-size=16384")
