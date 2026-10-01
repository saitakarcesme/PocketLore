#include "resource_budget.h"
#include <cassert>
#include <limits>
int main(){
    requireNativeBudget(2147483648ULL,805306368ULL,1073741824ULL);
    const uint64_t bad[][3]={{2147483649ULL,0,0},{0,805306369ULL,0},{0,0,1073741825ULL},{std::numeric_limits<uint64_t>::max(),0,0}};
    for(auto &v:bad){bool rejected=false;try{requireNativeBudget(v[0],v[1],v[2]);}catch(const std::runtime_error&){rejected=true;}assert(rejected);}
}
