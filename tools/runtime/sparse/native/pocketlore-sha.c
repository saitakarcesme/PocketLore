// Pinned upstream public-domain implementation, namespaced to avoid symbol interposition.
#define sha256_init pocketlore_sha256_init
#define sha256_update pocketlore_sha256_update
#define sha256_final pocketlore_sha256_final
#define sha256_hash pocketlore_sha256_hash
#include "../vendor/hash/sha256/sha256.c"
