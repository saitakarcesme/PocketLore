#pragma once
#include <cstdint>
#include <stdexcept>

#if defined(POCKETLORE_SCALE_SCREEN) && !defined(__ANDROID__)
constexpr uint64_t pocketloreModelLimit = 6000000000ULL;
#elif defined(POCKETLORE_HOST_SCREEN) && !defined(__ANDROID__)
constexpr uint64_t pocketloreModelLimit = 4294967296ULL;
#else
constexpr uint64_t pocketloreModelLimit = 2147483648ULL;
#endif

#if defined(POCKETLORE_SCALE_BUFFER_V2) && !defined(__ANDROID__)
// Host CPU repacking can retain mapped and transformed buffers simultaneously.
// The artifact file cap remains 6 GB; this is not an Android admission profile.
constexpr uint64_t pocketloreModelBufferLimit = 9000000000ULL;
#else
constexpr uint64_t pocketloreModelBufferLimit = pocketloreModelLimit;
#endif

// Shared by simulated-buffer preflight and post-allocation accounting.
inline void requireNativeBudget(uint64_t model,uint64_t kv,uint64_t compute) {
    if(model>pocketloreModelBufferLimit || kv>805306368ULL || compute>1073741824ULL)
        throw std::runtime_error("Runtime buffers exceed model/KV/compute resource budget; use a smaller model");
}

#if defined(POCKETLORE_SCALE_SCREEN) && !defined(__ANDROID__)
constexpr int pocketloreContextTokens=4096, pocketloreOutputTokens=512;
#else
constexpr int pocketloreContextTokens=2048, pocketloreOutputTokens=256;
#endif
