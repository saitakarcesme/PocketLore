#include "resource_budget.h"
#include <cassert>
int main(){
 requireNativeBudget(4242363904ULL,301989888,80413184,true);
 int denied=0;for(int i=0;i<4;i++)try{
  if(i==0)requireNativeBudget(4242363904ULL,301989888,80413184,false);
  if(i==1)requireNativeBudget(4600000001ULL,0,0,true);
  if(i==2)requireNativeBudget(1,805306369ULL,0,true);
  if(i==3)requireNativeBudget(1,0,1073741825ULL,true);
 }catch(const std::runtime_error&){denied++;}assert(denied==4);
 requirePinnedMemory(4242363904ULL,301989888,80413184,2497280256ULL,9500000000ULL,11482177536ULL);
 int ramDenied=0;for(int i=0;i<4;i++)try{
  requirePinnedMemory(4242363904ULL,301989888,80413184,i==0?2497280257ULL:2497280256ULL,i==1?0:9500000000ULL,i==2?12000000001ULL:(i==3?0:11482177536ULL));
 }catch(const std::runtime_error&){ramDenied++;}assert(ramDenied==4);
 assert(pocketloreModelLimit==2147483648ULL);assert(pocketloreContextTokens==2048);assert(pocketloreOutputTokens==256);
}
