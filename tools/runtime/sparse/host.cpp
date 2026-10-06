// Bounded diagnostic host execution; no product or support qualification.
#include "profile.h"
#include "scalar.h"
#include "pocketlore-owned.h"
#include "ggml-backend.h"
#include <fstream>
#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <csignal>
#include <sys/stat.h>
static pocketlore_sparse::LoadCancellation cancellation;
static void stop(int) { cancellation.requested.store(true); }
static bool abort_decode(void *) { return cancellation.requested.load(); }
static void phase(const char *s) { std::cerr << "POCKETLORE_PHASE " << s << std::endl; }
struct Backend {
 Backend(){ggml_backend_load_all();llama_backend_init();}
 ~Backend() noexcept {llama_backend_free();phase("backend_released");}
};
int execute(int argc,char **argv) {
 // Engineered exception path initializes only the backend, never model weights.
 if(argc==2 && (std::string(argv[1])=="--cleanup-cancel-control" || std::string(argv[1])=="--cleanup-expiry-control")){
  Backend backend;
  if(std::string(argv[1])=="--cleanup-cancel-control")cancellation.requested=true;
  throw std::runtime_error("Engineered cancellation/expiry before model admission");
 }

 if(argc!=5 || (std::string(argv[1])!="--exact-sparse-diagnostic" && std::string(argv[1])!="--exact-sparse-budget-diagnostic") || std::string(argv[3])!=pocketlore_sparse::weights_sha) return 2;
 signal(SIGTERM,stop);signal(SIGINT,stop);signal(SIGXCPU,stop);
 struct stat st{};if(stat(argv[2],&st)||uint64_t(st.st_size)!=pocketlore_sparse::file_bytes)return 3;
 std::ifstream input(argv[4]);std::string prompt((std::istreambuf_iterator<char>(input)),{});
 if(prompt.empty()||prompt.size()>16384)return 4;
 Backend backend;
 auto mp=llama_model_default_params();pocketlore_sparse::Identity id{pocketlore_sparse::file_bytes,argv[3],"qwen35moe",733};
 pocketlore_sparse::configure_experiment(mp,id,cancellation);phase("identity_hash");
 auto owner=pocketlore_owned::File::open(argv[2],argv[3],pocketlore_sparse::file_bytes,true,[]{return cancellation.requested.load();},180,[](){},pocketlore_owned::FaultPolicy::Random);
 if(std::string(argv[1])=="--exact-sparse-budget-diagnostic")owner->enable_budgeted_cache(2147483648ULL);
 const char *directory=getenv("POCKETLORE_OBSERVATIONS");
 auto observe=[&](const char *name){if(directory){std::ofstream f(std::string(directory)+"/"+name+".json");f<<owner->observation();std::ofstream cache(std::string(directory)+"/"+name+"-cache.json");cache<<owner->cache_observation();if(!f)throw std::runtime_error("Observation write failed");}};
 observe("verified");phase("loading");
 llama_model *model=nullptr;
 { pocketlore_owned::Scope scope(owner); model=llama_model_load_from_file(argv[2],mp); }
 std::unique_ptr<llama_model,decltype(&llama_model_free)> model_guard(model,llama_model_free);
 if(!model)return 5;
 owner->advise();observe("loaded");
 phase("loaded");std::this_thread::sleep_for(std::chrono::seconds(2));
 auto cp=llama_context_default_params();cp.n_ctx=1024;cp.n_batch=1;cp.n_ubatch=1;cp.n_threads=2;cp.n_threads_batch=2;cp.abort_callback=abort_decode;cp.abort_callback_data=nullptr;
 auto ctx=llama_init_from_model(model,cp);
 struct ContextCleanup {void operator()(llama_context *p)const noexcept {if(p){llama_synchronize(p);llama_free(p);phase("context_released");}}};
 std::unique_ptr<llama_context,ContextCleanup> context_guard(ctx);if(!ctx)return 6;
 auto vocab=llama_model_get_vocab(model);int n=-llama_tokenize(vocab,prompt.data(),prompt.size(),nullptr,0,true,true);
 if(n<=0||n>850)return 7;
 std::vector<llama_token> tokens(n);if(llama_tokenize(vocab,prompt.data(),prompt.size(),tokens.data(),n,true,true)!=n)return 8;
 // Only this diagnostic driver owns the context. Synchronize before releasing
 // the reader token; no mid-graph or expert eviction is permitted.
 int steps=0;
 auto decode=[&](llama_batch b){
  std::cerr<<"SCALAR_BEGIN "<<steps<<" "<<b.n_tokens<<std::endl;
  int result=pocketlore_sparse::scalar_step(owner,b.n_tokens,[&]{return llama_decode(ctx,b);},[&]{llama_synchronize(ctx);});
  std::cerr<<"SCALAR_END "<<steps++<<" "<<result<<std::endl;return result;};
 std::cerr<<"PREFILL_TOKENS "<<n<<std::endl;observe("prefill");phase("prefill");for(int i=0;i<n;++i){auto b=llama_batch_get_one(tokens.data()+i,1);if(decode(b))return 9;}
 auto sampler=llama_sampler_init_greedy();std::unique_ptr<llama_sampler,decltype(&llama_sampler_free)> sampler_guard(sampler,llama_sampler_free);observe("generation");phase("generation");int generated=0;bool ended=false;
 for(;generated<128&&!cancellation.requested;++generated){auto token=llama_sampler_sample(sampler,ctx,-1);if(llama_vocab_is_eog(vocab,token)){ended=true;break;}char b[4096];int len=llama_token_to_piece(vocab,token,b,sizeof b,0,true);if(len<0)return 10;std::cout.write(b,len);std::cout.flush();auto batch=llama_batch_get_one(&token,1);if(decode(batch))return 11;}
 std::cerr<<"POCKETLORE_TOKENS "<<generated<<" EOG "<<ended<<std::endl;phase("completed_hold");std::this_thread::sleep_for(std::chrono::seconds(2));
 observe("completed");sampler_guard.reset();context_guard.reset();model_guard.reset();observe("unmapped");phase("model_released");
 return cancellation.requested?12:0;
}

int main(int argc,char **argv) {
 int result=1;
 try { result=execute(argc,argv); }
 catch(const std::exception &e){std::cerr<<"DIAGNOSTIC_REFUSED "<<e.what()<<std::endl;result=cancellation.requested?12:13;}
 catch(...){std::cerr<<"DIAGNOSTIC_REFUSED unknown exception"<<std::endl;result=14;}
 phase("released_after_scope");return result;
}
