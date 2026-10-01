#pragma once
#include <cstdint>
#include <stdexcept>

// Shared by simulated-buffer preflight and post-allocation accounting.
inline void requireNativeBudget(uint64_t model,uint64_t kv,uint64_t compute) {
    if(model>2147483648ULL || kv>805306368ULL || compute>1073741824ULL)
        throw std::runtime_error("Runtime buffers exceed model/KV/compute resource budget; use a smaller model");
}
