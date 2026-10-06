#pragma once
// Linux/Android diagnostic-only verified descriptor and quiescent cache policy.
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <chrono>
#include <functional>
#include <memory>
#include <mutex>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <stdexcept>
#include <cstring>
#include <cstdio>
#define sha256_init pocketlore_sha256_init
#define sha256_update pocketlore_sha256_update
#define sha256_final pocketlore_sha256_final
#define sha256_hash pocketlore_sha256_hash
extern "C" {
#include "../vendor/hash/sha256/sha256.h"
}
#undef sha256_init
#undef sha256_update
#undef sha256_final
#undef sha256_hash
namespace pocketlore_owned {
inline std::string text(const std::string &p){std::ifstream f(p);if(!f)throw std::runtime_error("Unavailable kernel observation");return std::string(std::istreambuf_iterator<char>(f),{});}
inline std::string link(const std::string &p){char b[8192];auto n=readlink(p.c_str(),b,sizeof(b));if(n<0||n==sizeof(b))throw std::runtime_error("Unavailable link identity");return std::string(b,n);}
inline void require(bool b,const char *s){if(!b)throw std::runtime_error(s);}
inline std::string escape(const std::string&s){std::ostringstream o;o<<"\"";for(unsigned char c:s){if(c==34||c==92)o<<"\\"<<c;else if(c<32)o<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<int(c)<<std::dec;else o<<c;}return o.str()+"\"";}
inline bool same(const struct stat&a,const struct stat&b){return a.st_dev==b.st_dev&&a.st_ino==b.st_ino&&a.st_size==b.st_size&&a.st_mtim.tv_sec==b.st_mtim.tv_sec&&a.st_mtim.tv_nsec==b.st_mtim.tv_nsec&&a.st_ctim.tv_sec==b.st_ctim.tv_sec&&a.st_ctim.tv_nsec==b.st_ctim.tv_nsec&&a.st_nlink==b.st_nlink;}
class File:public std::enable_shared_from_this<File>{
 struct Region {void *address;size_t size;off_t offset;};
 int descriptor=-1;struct stat identity{};pid_t pid;std::string path,digest,mount,fdinfo,ns,start;
 std::mutex mutex;size_t readers=0;bool retiring=false;std::vector<Region> regions;bool full;std::function<bool()> cancel;std::chrono::steady_clock::time_point deadline;
 static std::string start_ticks(){auto s=text("/proc/self/stat");std::istringstream i(s.substr(s.rfind(')')+2));std::string v;for(int n=0;n<20;++n)i>>v;return v;}
 void budget(){require(!cancel()&&std::chrono::steady_clock::now()<deadline,"Cancelled or expired native operation");}
 explicit File(int fd,bool allow,std::function<bool()> stop,int seconds):descriptor(fd),pid(getpid()),full(allow),cancel(stop),deadline(std::chrono::steady_clock::now()+std::chrono::seconds(seconds)){
  require(fstat(fd,&identity)==0&&identity.st_nlink>0,"Missing descriptor");path=link("/proc/self/fd/"+std::to_string(fd));ns=link("/proc/self/ns/mnt")+link("/proc/self/ns/pid")+link("/proc/self/ns/user");start=start_ticks();fdinfo=text("/proc/self/fdinfo/"+std::to_string(fd));
  auto at=fdinfo.find("mnt_id:");require(at!=std::string::npos,"Missing mount ID");std::istringstream id(fdinfo.substr(at+7));std::string mid;id>>mid;std::istringstream lines(text("/proc/self/mountinfo"));for(std::string l;std::getline(lines,l);)if(l.substr(0,l.find(' '))==mid)mount=l;require(!mount.empty(),"Unknown mount");
 }
public:
 static std::shared_ptr<File> open(const char*path,const std::string&expected,uint64_t size,bool full,std::function<bool()>cancel,int seconds,std::function<void()>observe=[](){}){
  int fd=-1;std::string supplied(path);const std::string prefix="/proc/self/fd/";
  if(supplied.compare(0,prefix.size(),prefix)==0){auto tail=supplied.substr(prefix.size());require(!tail.empty()&&tail.find_first_not_of("0123456789")==std::string::npos,"Invalid explicit inherited descriptor");int inherited=std::stoi(tail);require((fcntl(inherited,F_GETFL)&O_ACCMODE)==O_RDONLY,"Inherited descriptor is not readonly");fd=fcntl(inherited,F_DUPFD_CLOEXEC,3);}
  else fd=::open(path,O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
  require(fd>=0,"Cannot open exact original");std::shared_ptr<File> p;
  try{p=std::shared_ptr<File>(new File(fd,full,cancel,seconds));}catch(...){::close(fd);throw;}
  require(uint64_t(p->identity.st_size)==size,"Wrong original length");sha256_t h;pocketlore_sha256_init(&h);std::vector<unsigned char>b(4*1024*1024);
  for(uint64_t off=0;off<size;){p->budget();size_t n=std::min<uint64_t>(b.size(),size-off);ssize_t got=pread(fd,b.data(),n,off);require(got==ssize_t(n),"Short original identity read");pocketlore_sha256_update(&h,b.data(),n);require(posix_fadvise(fd,off,n,POSIX_FADV_DONTNEED)==0,"Identity cache advice failed");off+=n;if(off%(64*1024*1024)==0)observe();}
  unsigned char out[32];pocketlore_sha256_final(&h,out);std::ostringstream hex;for(auto c:out)hex<<std::hex<<std::setw(2)<<std::setfill('0')<<int(c);p->digest=hex.str();require(p->digest==expected,"Wrong original digest");p->verify();return p;
 }
 ~File(){if(descriptor>=0)::close(descriptor);}
 bool exact()const{return identity.st_size==12290628576LL&&digest=="96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7";}
 int fd()const{return descriptor;}
 void verify(){budget();struct stat now{},named{};require(getpid()==pid&&start==start_ticks()&&ns==link("/proc/self/ns/mnt")+link("/proc/self/ns/pid")+link("/proc/self/ns/user"),"Changed namespace/owner");require(fstat(descriptor,&now)==0&&same(now,identity)&&stat(path.c_str(),&named)==0&&same(named,identity)&&link("/proc/self/fd/"+std::to_string(descriptor))==path,"Changed original version/path");}
 void verify_fd(int other){verify();struct stat s{};require(fstat(other,&s)==0&&same(s,identity),"Loader descriptor differs from verified original");}
 void validate_range(size_t n,off_t offset){verify();require(n && offset>=0 && uint64_t(offset)<=uint64_t(identity.st_size) && n<=uint64_t(identity.st_size)-uint64_t(offset) && offset%sysconf(_SC_PAGESIZE)==0 && (full ? exact() : n<=128*1024*1024),"Unsafe mapping range");}
 void register_mapping(void *p,size_t n,off_t offset){std::lock_guard<std::mutex>l(mutex);verify();require(regions.empty()&&!readers&&n&&offset>=0&&uint64_t(offset)+n<=uint64_t(identity.st_size)&&(full||n<=128*1024*1024),"Unsafe mapping registration");retiring=false;regions.push_back({p,n,offset});}
 void unregister_mapping(void*p){std::lock_guard<std::mutex>l(mutex);require(readers==0,"Cannot release mapping with live readers");for(auto i=regions.begin();i!=regions.end();++i)if(i->address==p){regions.erase(i);return;}throw std::runtime_error("Unknown mapping lifetime");}
 void inspect_region(void*p,size_t n,off_t offset){verify();std::istringstream lines(text("/proc/self/maps"));uintptr_t cursor=(uintptr_t)p,end=cursor+((n+sysconf(_SC_PAGESIZE)-1)/sysconf(_SC_PAGESIZE))*sysconf(_SC_PAGESIZE);std::istringstream mi(mount);std::string a,b,device;mi>>a>>b>>device;unsigned dm,dn;require(sscanf(device.c_str(),"%u:%u",&dm,&dn)==2,"Malformed mount device");
  for(std::string line;std::getline(lines,line);){unsigned long long lo,hi,off,ino;unsigned ma,mn;char perms[5]={};if(sscanf(line.c_str(),"%llx-%llx %4s %llx %x:%x %llu",&lo,&hi,perms,&off,&ma,&mn,&ino)!=7)continue;if(hi<=cursor||lo>=end)continue;require(lo==cursor&&hi<=end&&strcmp(perms,"r--s")==0&&ino==identity.st_ino&&ma==dm&&mn==dn&&off==uint64_t(offset)+lo-(uintptr_t)p,"Unbound partial/alias mapping");cursor=hi;}
  require(cursor==end,"Absent mapping");}
 // Cooperative diagnostic ownership only: final reader performs deferred
 // unmap. Destructors never throw or unmap memory still covered by a token.
 void finish_retire_locked() noexcept {
  if(!retiring||readers)return;
  for(auto &r:regions)if(munmap(r.address,r.size)!=0)std::fprintf(stderr,"OWNED_UNMAP_FAILURE\n");
  regions.clear();
 }
 void release_reader() noexcept {
  try {std::lock_guard<std::mutex>l(mutex);if(readers)--readers;finish_retire_locked();}
  catch (...) {std::fprintf(stderr,"OWNED_READER_CLEANUP_REFUSED\n");}
 }
 void retire(void *address) noexcept {
  try {std::lock_guard<std::mutex>l(mutex);if(regions.size()!=1||regions[0].address!=address){std::fprintf(stderr,"OWNED_UNKNOWN_RELEASE_REFUSED\n");return;}retiring=true;finish_retire_locked();}
  catch (...) {std::fprintf(stderr,"OWNED_RELEASE_REFUSED\n");}
 }
 class Use{std::shared_ptr<File>p;public:explicit Use(std::shared_ptr<File>x):p(x){std::lock_guard<std::mutex>l(p->mutex);p->verify();require(!p->retiring&&!p->regions.empty(),"No live owned mapping for reader");++p->readers;}Use(const Use&)=delete;~Use() noexcept {p->release_reader();}};
 Use use(){return Use(shared_from_this());}
 void advise(){std::lock_guard<std::mutex>l(mutex);verify();require(!retiring&&!readers,"Alias, retiring mapping or async reader still active");const size_t page=sysconf(_SC_PAGESIZE);
  require(!regions.empty(),"No owned mappings");for(auto&r:regions){inspect_region(r.address,r.size,r.offset);require(r.offset%page==0,"Unaligned file offset");for(size_t off=0;off<r.size;){budget();size_t n=std::min<size_t>(128*1024*1024,r.size-off);require(madvise((char*)r.address+off,n,MADV_DONTNEED)==0,"Targeted mapping advice failed");require(posix_fadvise(descriptor,r.offset+off,n,POSIX_FADV_DONTNEED)==0,"Targeted file advice failed");off+=n;}}
 }
 std::string observation(){std::lock_guard<std::mutex> lock(mutex);verify();std::ostringstream r;r<<"[";bool comma=false;for(auto &v:regions){if(comma)r<<",";comma=true;size_t page=sysconf(_SC_PAGESIZE),count=(v.size+page-1)/page;std::vector<unsigned char> bits(count);require(mincore(v.address,v.size,bits.data())==0,"Cache residency unavailable");size_t present=0;for(auto b:bits)present+=b&1;r<<"{\"address\":"<<(uintptr_t)v.address<<",\"bytes\":"<<v.size<<",\"offset\":"<<v.offset<<",\"page_size\":"<<page<<",\"cache_present_pages\":"<<present<<"}";}r<<"]";std::ostringstream o;o<<"{\"monotonic_ns\":"<<std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count()<<",\"regions\":"<<r.str()<<",";o<<"\"pid\":"<<pid<<",\"startticks\":"<<escape(start)<<",\"fd\":"<<descriptor<<",\"stat_device\":"<<identity.st_dev<<",\"inode\":"<<identity.st_ino<<",\"bytes\":"<<identity.st_size<<",\"sha256\":"<<escape(digest)<<",\"fdinfo\":"<<escape(fdinfo)<<",\"mount\":"<<escape(mount)<<",\"namespaces\":"<<escape(ns)<<",\"smaps\":"<<escape(text("/proc/self/smaps"))<<",\"status\":"<<escape(text("/proc/self/status"))<<"}";return o.str();}
};
// Thread-local loader scope cannot adopt mappings created by another call/thread.
inline thread_local std::shared_ptr<File> active;
inline thread_local size_t window_size=0, window_offset=0;
class Scope {
public:
 Scope(std::shared_ptr<File> f,size_t size=0,size_t offset=0){require(!active,"Nested mapping owner");require(size || f->exact(),"Full diagnostic owner must be exact model");f->validate_range(size ? size : 12290628576ULL,offset);active=f;window_size=size;window_offset=offset;}
 ~Scope(){active.reset();window_size=window_offset=0;}
 Scope(const Scope&)=delete;
};
}

