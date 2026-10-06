// Synthetic-only native fault policy controls; never accepts an actual model.
#include "pocketlore-owned.h"
#include "llama-mmap.h"
#include <iostream>
#include <thread>
#include <atomic>
#include <sys/wait.h>
#include <sys/prctl.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sys/syscall.h>
#include <cstddef>
using namespace pocketlore_owned;
static constexpr size_t SIZE=64*1024*1024;
static const size_t pages[]={17,1041,2065,3089,4113,5137,6161,7185,8209,9233,10257,11281,12305,13329,14353,15377};
static void refused(const char*n,std::function<void()> f){bool bad=false;try{f();}catch(const std::exception&e){bad=true;std::cout<<"{\"refusal\":"<<escape(n)<<",\"reason\":"<<escape(e.what())<<"}\n";}require(bad,"Control unexpectedly accepted");}
static unsigned char oracle(size_t i){return ((i*73)^(i>>8)^(i>>16))&255;}
static void record(const std::string&prefix,const std::string&phase,std::shared_ptr<File>f,void*addr){
 std::vector<unsigned char> bits(SIZE/4096);require(mincore(addr,SIZE,bits.data())==0,"mincore failed");
 std::ofstream out(prefix+"-"+phase+".json");out<<"{\"owner\":"<<f->observation()<<",\"cached_pages\":[";bool comma=false;
 for(size_t i=0;i<bits.size();++i)if(bits[i]&1){if(comma)out<<",";out<<i;comma=true;}out<<"]}";require(bool(out),"Observation write failed");
}
static void block_advice(bool mapping){
 // Child-only kernel failure injection, not a production policy toggle.
 sock_filter filter[]={BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(seccomp_data,nr)),
 BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,mapping?SYS_madvise:SYS_fadvise64,0,3),
 BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(seccomp_data,args)+(mapping?2:3)*sizeof(uint64_t)),
 BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,mapping?MADV_RANDOM:POSIX_FADV_RANDOM,0,1),
 BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EPERM),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW)};
 sock_fprog p{(unsigned short)(sizeof(filter)/sizeof(filter[0])),filter};require(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)==0 && prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&p)==0,"Cannot install owned child failure control");
}
int main(int argc,char**argv){try{
 require(argc==5,"fixture SHA policy prefix required");struct stat initial{};require(stat(argv[1],&initial)==0&&initial.st_size==SIZE,"Only fixed synthetic size allowed");require(sysconf(_SC_PAGESIZE)==4096,"Unsupported page-size fixture");
 std::string mode=argv[3],prefix=argv[4];require(mode=="default"||mode=="random"||mode=="negative","Unknown fixture policy");bool cancel=false;
 if(mode=="negative"){
  for(bool mapping:{false,true}){
   pid_t p=fork();require(p>=0,"Cannot fork owned control");if(p==0){
    try{block_advice(mapping);auto f=File::open(argv[1],argv[2],SIZE,false,[]{return false;},30,[](){},FaultPolicy::Random);
     Scope scope(f,SIZE);llama_file file(argv[1],"rb");llama_mmap map(&file,0,false);_exit(3);
    }catch(const std::exception&e){std::string msg=e.what();bool exact=msg==(mapping?"Owned MADV_RANDOM failed":"Dedicated POSIX_FADV_RANDOM failed");std::cerr<<"KERNEL_POLICY_REFUSAL "<<msg<<std::endl;_exit(exact?0:4);}
   }int status=0;require(waitpid(p,&status,0)==p&&WIFEXITED(status)&&WEXITSTATUS(status)==0,"Policy syscall failure control failed");std::cout<<"{\"refusal\":\""<<(mapping?"madvise-kernel-failure":"fadvise-kernel-failure")<<"\",\"child\":"<<p<<",\"exit\":0}\n";
  }
  int inherited=::open(argv[1],O_RDONLY|O_CLOEXEC);require(inherited>=0,"Cannot open inherited fixture");std::string inherited_path="/proc/self/fd/"+std::to_string(inherited);
  auto f=File::open(inherited_path.c_str(),argv[2],SIZE,false,[&]{return cancel;},30,[](){},FaultPolicy::Random);
  require(lseek(f->fd(),123,SEEK_SET)==123&&lseek(inherited,0,SEEK_CUR)==0,"Descriptor shares caller offset");
  refused("double-owner",[&]{File::open(argv[1],argv[2],SIZE,false,[]{return false;},30,[](){},FaultPolicy::Random);});
  int writable=::open(argv[1],O_RDWR|O_CLOEXEC);require(writable>=0,"Cannot open owned readonly-negative handle");std::string wp="/proc/self/fd/"+std::to_string(writable);
  refused("writable-inherited",[&]{File::open(wp.c_str(),argv[2],SIZE,false,[]{return false;},30,[](){},FaultPolicy::Random);});::close(writable);
  {Scope scope(f,SIZE);llama_file file(argv[1],"rb");llama_mmap map(&file,0,false);auto use=f->use();refused("live-reader-advice",[&]{f->advise();});refused("alias",[&]{llama_mmap alias(&file,0,false);});}
  {Scope scope(f,SIZE);llama_file file(argv[1],"rb");llama_mmap map(&file,0,false);cancel=true;refused("cancel",[&]{f->advise();});cancel=false;}
  {Scope scope(f,SIZE);llama_file file(argv[1],"rb");try{llama_mmap map(&file,0,false);throw std::runtime_error("fixture");}catch(...){refused("exception-release",[&]{f->advise();});}}
  f.reset();::close(inherited);
  refused("hash",[&]{File::open(argv[1],std::string(64,'0'),SIZE,false,[]{return false;},30,[](){},FaultPolicy::Random);});
  refused("deadline",[&]{File::open(argv[1],argv[2],SIZE,false,[]{return false;},0,[](){},FaultPolicy::Random);});
  std::cout<<"{\"control\":\"dedicated-reuse-offset\",\"pass\":true}\n";return 0;
 }
 auto f=File::open(argv[1],argv[2],SIZE,false,[&]{return cancel;},60,[](){},mode=="random"?FaultPolicy::Random:FaultPolicy::Default);
 for(int round=0;round<2;++round){
  Scope scope(f,SIZE);llama_file file(argv[1],"rb");llama_mmap map(&file,0,false);f->advise();
  std::vector<unsigned char> bits(SIZE/4096);require(mincore(map.addr(),SIZE,bits.data())==0,"Cold mincore failed");for(auto b:bits)require(!(b&1),"Cold start unavailable");
  std::string run=prefix+"-"+std::to_string(round);record(run,"cold",f,map.addr());
  uint64_t sum=0;{auto use=f->use();for(size_t page:pages)for(size_t j=0;j<4096;++j){size_t offset=page*4096+j;unsigned char actual=((volatile unsigned char*)map.addr())[offset];require(actual==oracle(offset),"Mapped byte oracle mismatch");sum+=actual;}}
  std::this_thread::sleep_for(std::chrono::milliseconds(100));record(run,"touched",f,map.addr());
  std::this_thread::sleep_for(std::chrono::milliseconds(200));f->advise();record(run,"released",f,map.addr());
  {auto use=f->use();for(size_t page:pages){unsigned char value;require(pread(f->fd(),&value,1,page*4096)==1 && value==((unsigned char*)map.addr())[page*4096] && value==oracle(page*4096),"Post-advice bytes changed");}}
  f->advise();std::cout<<"{\"round\":"<<round<<",\"bytes_compared\":65536,\"sum\":"<<sum<<",\"post_advice_matches\":16}\n";
 }
 std::cout<<"{\"status\":\"FAULT_CONTROLS_PASS\"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"FAULT_REFUSED "<<e.what()<<std::endl;return 1;}}
