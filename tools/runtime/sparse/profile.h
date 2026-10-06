#pragma once
#include <cstdint>
#include <atomic>
#include <stdexcept>
#include <string>
#include "llama.h"

// Experimental exact identity only. This is not production model admission.
namespace pocketlore_sparse {
constexpr uint64_t file_bytes = 12290628576ULL;
constexpr const char * weights_sha = "96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7";
struct Identity { uint64_t bytes; std::string sha, architecture; uint32_t tensors; };
// Caller retains this object until the synchronous loader has returned.
struct LoadCancellation { std::atomic<bool> requested{false}; };
inline bool continue_load(float, void *data) {
    return data && !static_cast<LoadCancellation *>(data)->requested.load(std::memory_order_relaxed);
}
inline void configure_experiment(llama_model_params &p, const Identity &id, LoadCancellation &cancel) {
    if (id.bytes != file_bytes || id.sha != weights_sha || id.architecture != "qwen35moe" || id.tensors != 733)
        throw std::runtime_error("Unknown sparse model identity");
    p.load_mode = LLAMA_LOAD_MODE_MMAP;
    p.prefetch_mmap = false;
    p.progress_callback = continue_load;
    p.progress_callback_user_data = &cancel;
    p.use_extra_bufts = false;
    p.check_tensors = false; // Already false upstream; not a newly disabled scan.
    p.n_gpu_layers = 0;
}
struct ResidentWindow {
    uint64_t rss, pss, anonymous, model_file_rss, other_file_rss, swap;
    uint64_t aggregate_kernel_peak, device_total, os_available;
    bool complete_same_pid_window;
};
inline void verify_window(const ResidentWindow &w) {
    constexpr uint64_t cap=12000000000ULL, reserve=1073741824ULL;
    // Virtual mapping span and expert-use ratio are deliberately not inputs.
    if (!w.complete_same_pid_window || !w.rss || !w.pss || !w.aggregate_kernel_peak ||
        w.pss>w.rss || w.anonymous>w.rss || w.model_file_rss>w.rss-w.anonymous ||
        w.other_file_rss!=w.rss-w.anonymous-w.model_file_rss || w.swap ||
        w.device_total>cap || w.device_total<=reserve || w.os_available<reserve ||
        w.rss>w.aggregate_kernel_peak || w.aggregate_kernel_peak>w.device_total-reserve)
        throw std::runtime_error("Incomplete or over-budget resident window");
}
// A passing sample is necessary but never sufficient for load, history or quality admission.
constexpr bool production_admitted = false;
}
