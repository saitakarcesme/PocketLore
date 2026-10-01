#pragma once
#include <cstdint>
#include <stdexcept>

#if defined(POCKETLORE_HOST_SCREEN) && !defined(__ANDROID__)
constexpr uint64_t pocketloreModelLimit = 4294967296ULL;
#else
constexpr uint64_t pocketloreModelLimit = 2147483648ULL;
#endif

// Shared by simulated-buffer preflight and post-allocation accounting.
inline void requireNativeBudget(uint64_t model,uint64_t kv,uint64_t compute) {
    if(model>pocketloreModelLimit || kv>805306368ULL || compute>1073741824ULL)
        throw std::runtime_error("Runtime buffers exceed model/KV/compute resource budget; use a smaller model");
}
