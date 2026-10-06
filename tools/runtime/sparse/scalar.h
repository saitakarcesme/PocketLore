#pragma once
#include "pocketlore-owned.h"
// Universal diagnostic scheduling: one token, synchronized completion, then
// relinquish the sole reader before targeted advice. Never evict mid-graph.
namespace pocketlore_sparse {
template<class Decode,class Sync>
int scalar_step(const std::shared_ptr<pocketlore_owned::File>& owner,
                int count, Decode decode, Sync synchronize) {
 pocketlore_owned::require(count==1,"Scalar diagnostic requires exactly one token");
 int result;
 {auto reader=owner->use();
  try {result=decode();} catch (...) {synchronize();throw;}
  synchronize();
 }
 owner->advise();return result;
}
}
