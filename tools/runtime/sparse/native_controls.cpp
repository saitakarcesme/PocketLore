// Native algorithm controls, never model loading or generation.
#include "pocketlore-owned.h"
#include "llama-mmap.h"
#include <iostream>
#include <atomic>
#include <thread>
using namespace pocketlore_owned;
static void denied(const char *name,std::function<void()> action){bool refused=false;try{action();}catch(const std::exception&e){refused=true;std::cout<<"{\"control\":"<<escape(name)<<",\"refused\":true,\"reason\":"<<escape(e.what())<<"}\n";}require(refused,"Negative control unexpectedly succeeded");}
int main(int argc,char**argv){try{
 require(argc==6,"path SHA size output-prefix offset required");std::string path=argv[1];uint64_t bytes=std::stoull(argv[3]);std::atomic<bool> cancelled{false};
 auto observe=[&](){std::ofstream log(std::string(argv[4])+"-hash-status.txt",std::ios::app);log<<std::chrono::steady_clock::now().time_since_epoch().count()<<" PID "<<getpid()<<"\n"<<text("/proc/self/status")<<text("/proc/self/cgroup");};
 auto f=File::open(argv[1],argv[2],bytes,false,[&]{return cancelled.load();},300,observe);
 const size_t window=4*1024*1024;const size_t offset=std::stoull(argv[5]);require(bytes>=window,"Control needs four MiB");
 denied("unaligned",[&]{Scope s(f,window,1);});
 denied("oversized",[&]{Scope s(f,129*1024*1024);});
 denied("absent-map",[&]{f->advise();});
 {
 Scope scope(f,window,offset);llama_file file(argv[1],"rb");llama_mmap map(&file,0,false);
 std::vector<unsigned char> expected(window);require(pread(f->fd(),expected.data(),window,offset)==ssize_t(window),"Short oracle read");
 {auto use=f->use();require(memcmp(expected.data(),map.addr(),window)==0,"Mapped bytes differ from pread");}
 f->inspect_region(map.addr(),window,offset);
 {std::ostringstream path;path<<"/proc/self/map_files/"<<std::hex<<(uintptr_t)map.addr()<<"-"<<((uintptr_t)map.addr()+window);struct stat info{};int rc=stat(path.str().c_str(),&info),error=errno;std::ofstream out(std::string(argv[4])+"-map-files.json");out<<"{\"link\":"<<escape(link(path.str()))<<",\"stat_result\":"<<rc<<",\"errno\":"<<error<<"}";}

 std::ofstream(std::string(argv[4])+"-resident.json")<<f->observation();std::this_thread::sleep_for(std::chrono::milliseconds(300));
 std::atomic<bool> ready{false},release{false};std::thread worker([&]{auto u=f->use();ready=true;while(!release.load())std::this_thread::yield();});while(!ready.load())std::this_thread::yield();
 denied("async-reader",[&]{f->advise();});release=true;worker.join();
 denied("alias-mapping",[&]{llama_mmap alias(&file,0,false);});
 {auto u=f->use();denied("live-lifetime",[&]{f->unregister_mapping(map.addr());});}
 denied("nested-owner",[&]{Scope nested(f,window);});
 denied("partial-map",[&]{f->inspect_region(map.addr(),window/2,offset);});
 f->advise();std::ofstream(std::string(argv[4])+"-released.json")<<f->observation();std::this_thread::sleep_for(std::chrono::milliseconds(300));
 {auto use=f->use();require(memcmp(expected.data(),map.addr(),window)==0,"Cache advice changed original bytes");}
 cancelled=true;denied("cancelled",[&]{f->advise();});cancelled=false;
 std::cout<<"{\"control\":\"mapped-pread-after-advice\",\"pass\":true,\"payload_read_bytes\":"<<3*window<<"}\n";
 }
 denied("closed-map",[&]{f->advise();});denied("reader-after-unregister",[&]{auto use=f->use();});f->verify();
 if(bytes==4*1024*1024){
 {
  Scope scope(f,window);llama_file file(argv[1],"rb");auto map=std::make_unique<llama_mmap>(&file,0,false);void *address=map->addr();
  auto reader=std::make_unique<File::Use>(f);std::atomic<bool> done{false};
  std::thread observer([&]{for(int i=0;i<20;++i){auto observation=f->observation();require(!observation.empty(),"Empty observation");}done=true;});
  map.reset();denied("retiring-reader",[&]{auto u=f->use();});denied("retiring-advice",[&]{f->advise();});
  unsigned char check;require(pread(f->fd(),&check,1,0)==1 && *(volatile unsigned char*)address==check,"Deferred mapping lost bytes");
  observer.join();require(done,"Observer incomplete");reader.reset();
  unsigned char present;errno=0;require(mincore(address,4096,&present)==-1&&errno==ENOMEM,"Deferred unmap incomplete");
  std::cout<<"{\"control\":\"deferred-destructor-observation\",\"pass\":true}\n";
 }
 try {Scope scope(f,window);llama_file file(argv[1],"rb");llama_mmap map(&file,0,false);cancelled=true;f->advise();throw std::runtime_error("Unexpected cancellation success");}
 catch(const std::exception &){cancelled=false;denied("exception-unmapped",[&]{f->advise();});}

 int unrelated=::open("/dev/null",O_RDONLY|O_CLOEXEC);require(unrelated>=0,"Cannot open distractor");denied("wrong-inode",[&]{f->verify_fd(unrelated);});::close(unrelated);
 auto inherited=File::open(("/proc/self/fd/"+std::to_string(f->fd())).c_str(),argv[2],bytes,false,[]{return false;},10);inherited->verify_fd(f->fd());
 std::cout<<"{\"control\":\"inherited-fd\",\"pass\":true}\n";

 denied("wrong-size",[&]{File::open(argv[1],argv[2],bytes+1,false,[]{return false;},10);});
 denied("wrong-hash",[&]{File::open(argv[1],std::string(64,'0'),bytes,false,[]{return false;},10);});
 denied("deadline",[&]{File::open(argv[1],argv[2],bytes,false,[]{return false;},0);});
 require(rename(argv[1],(path+".retained-renamed").c_str())==0,"Cannot retain renamed fixture");
 denied("renamed",[&]{f->verify();});
 }

 std::cout<<"{\"status\":\"NATIVE_CONTROLS_PASS\",\"inference\":false}\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
