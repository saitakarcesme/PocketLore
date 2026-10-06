// Fixed synthetic native cache experiment; no model-sized input is accepted.
#include "pocketlore-owned.h"
#include "llama-mmap.h"
#include "scalar.h"
#include <iostream>
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <sys/syscall.h>
#include <cstddef>
using namespace pocketlore_owned;
static constexpr size_t size=33554432;
static unsigned char byte(size_t i){return ((i*73)^(i>>8)^(i>>16))&255;}
static uint64_t clock_ns(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
static void inject(const std::string&mode){
 unsigned call=mode=="mincore-failure"?SYS_mincore:SYS_madvise;
 unsigned action=mode=="no-progress"?SECCOMP_RET_ERRNO:SECCOMP_RET_ERRNO|EPERM;
 std::vector<sock_filter> v;
 auto block=[&](unsigned syscall){v.push_back(BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(seccomp_data,nr)));v.push_back(BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,syscall,0,1));v.push_back(BPF_STMT(BPF_RET|BPF_K,action));};
 block(call);if(mode=="no-progress")block(SYS_fadvise64);v.push_back(BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW));
 sock_fprog p{(unsigned short)v.size(),v.data()};require(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)==0&&prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&p)==0,"Fixture seccomp unavailable");
}
static void snapshot(const std::string&p,std::shared_ptr<File>owner,void*address){
 std::vector<unsigned char>b(size/4096);require(mincore(address,size,b.data())==0,"Independent mincore failed");std::ofstream f(p);f<<"{\"owner\":"<<owner->observation()<<",\"cache\":"<<owner->cache_observation()<<",\"stat\":"<<escape(text("/proc/self/stat"))<<",\"cached_pages\":[";bool comma=false;for(size_t i=0;i<b.size();++i)if(b[i]&1){if(comma)f<<",";f<<i;comma=true;}f<<"]}";require(bool(f),"Snapshot write failure");
}
int main(int argc,char**argv){try{
 require(argc==5,"fixture hash mode prefix required");struct stat s{};require(stat(argv[1],&s)==0&&s.st_size==size&&sysconf(_SC_PAGESIZE)==4096,"Fixed synthetic fixture required");
 std::string mode=argv[3],prefix=argv[4];require(mode=="remap"||mode=="tail"||mode=="force"||mode=="retain"||mode=="no-progress"||mode=="mincore-failure"||mode=="advice-failure","Invalid fixture mode");
 bool cancelled=false;auto owner=File::open(argv[1],argv[2],size,false,[&]{return cancelled;},30,[](){},FaultPolicy::Random);
 if(mode!="force")owner->enable_budgeted_cache(8388608);
 llama_file file(argv[1],"rb");std::unique_ptr<llama_mmap>map;{Scope scope(owner,mode=="tail"?size-1056:size);map.reset(new llama_mmap(&file,0,false));}
 auto address=(volatile unsigned char*)map->addr();snapshot(prefix+"-cold.json",owner,map->addr());
 if(mode=="remap"){
  {auto use=owner->use();for(size_t i=0;i<16777216;++i)require(address[i]==byte(i),"Remap byte oracle");}owner->advise();
  std::cout<<"{\"before_remap\":"<<owner->cache_observation()<<"}\n";map.reset();{Scope scope(owner,4194304);map.reset(new llama_mmap(&file,0,false));}
  address=(volatile unsigned char*)map->addr();{auto use=owner->use();for(size_t i=0;i<4194304;++i)require(address[i]==byte(i),"Remapped byte oracle");}owner->advise();
  std::cout<<"{\"remapped\":"<<owner->observation()<<",\"cache\":"<<owner->cache_observation()<<"}\n";return 0;
 }
 if(mode=="tail"){
  {auto use=owner->use();for(size_t i=0;i<16777216;++i)require(address[i]==byte(i),"Tail byte oracle");require(address[size-1057]==byte(size-1057),"Tail boundary byte");}
  owner->advise();snapshot(prefix+"-tail.json",owner,map->addr());std::cout<<"{\"tail_bytes\":"<<size-1056<<",\"cache\":"<<owner->cache_observation()<<"}\n";return 0;
 }
 if(mode!="force"&&mode!="retain"){
  {auto use=owner->use();for(size_t i=0;i<16777216;++i)require(address[i]==byte(i),"Negative byte oracle");}
  inject(mode);bool failed=false;try{owner->advise();}catch(const std::exception&e){failed=true;std::cout<<"{\"expected_refusal\":"<<escape(mode)<<",\"reason\":"<<escape(e.what())<<",\"cache\":"<<owner->cache_observation()<<"}\n";}require(failed,"Injected policy failure passed");return 0;
 }
 const size_t offsets[]={0,0,4194304,0,16777216,16777216};const size_t lengths[]={4194304,4194304,12582912,4194304,16777216,4194304};
 for(int step=0;step<6;++step){
  snapshot(prefix+"-"+std::to_string(step)+"-before.json",owner,map->addr());rusage a{},b{};getrusage(RUSAGE_SELF,&a);auto start=clock_ns();uint64_t sum=0;
  int rc=pocketlore_sparse::scalar_step(owner,1,[&]{for(size_t i=offsets[step];i<offsets[step]+lengths[step];++i){auto v=address[i];require(v==byte(i),"Original byte mismatch");sum+=v;}snapshot(prefix+"-"+std::to_string(step)+"-touched.json",owner,map->addr());return 0;},[](){});
  auto end=clock_ns();getrusage(RUSAGE_SELF,&b);require(rc==0,"Scalar failure");snapshot(prefix+"-"+std::to_string(step)+"-after.json",owner,map->addr());
  std::cout<<"{\"step\":"<<step<<",\"offset\":"<<offsets[step]<<",\"bytes\":"<<lengths[step]<<",\"sum\":"<<sum<<",\"start_ns\":"<<start<<",\"end_ns\":"<<end<<",\"major_faults\":"<<b.ru_majflt-a.ru_majflt<<",\"minor_faults\":"<<b.ru_minflt-a.ru_minflt<<",\"cpu_us\":"<<(b.ru_utime.tv_sec-a.ru_utime.tv_sec+b.ru_stime.tv_sec-a.ru_stime.tv_sec)*1000000LL+b.ru_utime.tv_usec-a.ru_utime.tv_usec+b.ru_stime.tv_usec-a.ru_stime.tv_usec<<"}\n";
 }
 map.reset();std::cout<<"{\"released\":true,\"owner\":"<<owner->observation()<<"}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"REFUSED "<<e.what()<<"\n";return 1;}}
