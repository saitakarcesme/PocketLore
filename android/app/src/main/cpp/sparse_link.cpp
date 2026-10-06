// Linked diagnostic policy only; normal JNI model admission remains unchanged.
#include "../../../../../tools/runtime/sparse/profile.h"
extern "C" __attribute__((visibility("default"))) bool pocketlore_sparse_diagnostic_parameters(
    llama_model_params *params, const pocketlore_sparse::Identity *identity,
    pocketlore_sparse::LoadCancellation *cancel) {
    if (!params || !identity || !cancel) return false;
    try { pocketlore_sparse::configure_experiment(*params, *identity, *cancel); return true; }
    catch (...) { return false; }
}
