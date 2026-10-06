// Synthetic control evidence only; never changes loader policy or reads a model.
#pragma once
#include "pocketlore-owned.h"
#include <regex>
namespace auxiliary_trace {
using namespace pocketlore_owned;
inline std::string prefix;
inline unsigned sequence=0;
inline std::weak_ptr<File> owner;
inline void record(const std::string &operation,const std::string &outcome,const std::string &reason="") {
 std::ostringstream o;auto f=owner.lock();struct stat st{};int fd=f?f->fd():-1;
 o<<"{\"sequence\":"<<sequence++<<",\"pid\":"<<getpid()<<",\"monotonic_ns\":"<<std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count()<<",\"operation\":"<<escape(operation)<<",\"outcome\":"<<escape(outcome)<<",\"reason\":"<<escape(reason)
 <<",\"stat\":"<<escape(text("/proc/self/stat"))<<",\"status\":"<<escape(text("/proc/self/status"))<<",\"namespaces\":"<<escape(link("/proc/self/ns/mnt")+link("/proc/self/ns/pid")+link("/proc/self/ns/user"))<<",\"cgroup\":"<<escape(text("/proc/self/cgroup"));
 o<<",\"owner_present\":"<<(f?"true":"false");
 if(f){if(operation=="verified")o<<",\"verified_owner\":"<<f->observation();require(fstat(fd,&st)==0,"Trace fstat failed");auto fi=text("/proc/self/fdinfo/"+std::to_string(fd));
  o<<",\"fd\":"<<fd<<",\"fdinfo\":"<<escape(fi)<<",\"inode\":"<<st.st_ino<<",\"device\":"<<st.st_dev<<",\"size\":"<<st.st_size<<",\"mtime_ns\":"<<(uint64_t(st.st_mtim.tv_sec)*1000000000+st.st_mtim.tv_nsec)<<",\"mountinfo\":"<<escape(text("/proc/self/mountinfo"));
  std::istringstream lines(text("/proc/self/smaps"));std::string selected;bool take=false;
  for(std::string l;std::getline(lines,l);){unsigned long a,b,offset,inode;unsigned d,e;char perms[8];
   if(sscanf(l.c_str(),"%lx-%lx %7s %lx %x:%x %lu",&a,&b,perms,&offset,&d,&e,&inode)==7)take=inode==st.st_ino;
   if(take)selected+=l+"\n";
  }o<<",\"owned_smaps\":"<<escape(selected);
 }
 o<<"}\n";auto bytes=o.str();require(bytes.size()<=262144,"Trace record bound");
 std::ofstream out(prefix+"-trace-"+std::to_string(getpid())+".json",std::ios::app);out<<bytes;out.flush();require(bool(out),"Trace write failed");
}
inline void begin(const std::string&p){prefix=p;record("process","begin");}
inline void refusal(const char*name,std::function<void()> action){
 record(name,"begin");try{action();}catch(const std::exception&e){record(name,"refused",e.what());return;}
 record(name,"unexpected-success");throw std::runtime_error("Negative control unexpectedly succeeded");
}
}
