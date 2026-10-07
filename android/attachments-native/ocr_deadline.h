#pragma once
#include <atomic>
#include <chrono>
#include <cstdint>
#include <stdexcept>
namespace attachment_ocr {
inline int64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
// Relative duration only: Java and native monotonic epochs are never compared.
class Deadline {
 int64_t start_,budget_; const std::atomic<bool>& cancel_;
 public:
 Deadline(int64_t remaining,const std::atomic<bool>& cancel,int64_t start=now()):start_(start),budget_(remaining),cancel_(cancel){if(remaining<=0||remaining>30000000000LL)throw std::runtime_error("Invalid OCR remaining budget");}
 int64_t remaining(int64_t tick)const{if(cancel_.load()||tick<start_)return 0;uint64_t elapsed=uint64_t(tick)-uint64_t(start_);return elapsed>=uint64_t(budget_)?0:budget_-int64_t(elapsed);}
 void check()const{if(!remaining(now()))throw std::runtime_error("OCR cancelled or expired");}
 int milliseconds(int64_t tick)const{return int(remaining(tick)/1000000);}
 bool stopped()const{return !remaining(now());}
};
}
