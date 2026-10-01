#include <jni.h>
#include "llama.h"
#include "llama-ext.h"
#include "resource_budget.h"
#include <atomic>
#include <cstdlib>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include <sys/stat.h>

namespace {
std::atomic<int> residentCount{0};
struct Session {
    Session(){++residentCount;}
    std::atomic<bool> cancelled{false};
    std::mutex operation;
    llama_model *model = nullptr;
    ~Session() { if (model) llama_model_free(model); --residentCount; }
};
std::mutex registryMutex;
std::unordered_map<jlong, std::shared_ptr<Session>> sessions;
jlong nextId = 1;
std::once_flag backendOnce;
std::atomic<int> activeContexts{0};
// Read-only lifecycle observations: idle, preflight, weight load, context, prefill, decode.
std::atomic<int> phase{0};
std::atomic<uint64_t> loadCallbacks{0},abortCallbacks{0},promptTokens{0},contextAttempts{0},allocationFailures{0};
std::atomic<uint64_t> estimatedModel{0},estimatedKV{0},estimatedCompute{0};
struct PhaseScope { explicit PhaseScope(int value){phase=value;loadCallbacks=0;abortCallbacks=0;promptTokens=0;} ~PhaseScope(){phase=0;} };
int runtimeThreads() {
#if defined(POCKETLORE_HOST_SCREEN) && !defined(__ANDROID__)
    const char *value=std::getenv("POCKETLORE_HOST_THREADS");
    const std::string threads=value?value:"6";
    if(threads.size()!=1 || threads[0]<'1' || threads[0]>'6')throw std::runtime_error("Host threads must be 1 through 6");
    return threads[0]-'0';
#else
    return 2;
#endif
}
llama_context_params contextParams() {
    auto p=llama_context_default_params();
    p.n_ctx=2048;p.n_batch=2048;p.n_ubatch=128;p.n_seq_max=1;p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;
    p.n_threads=runtimeThreads();p.n_threads_batch=runtimeThreads();return p;
}
std::atomic<uint64_t> contextBytes{0},computeBytes{0},modelBufferBytes{0};
void releaseContext(llama_context *ctx){if(ctx){llama_free(ctx);--activeContexts;contextBytes=0;computeBytes=0;modelBufferBytes=0;}}
std::shared_ptr<Session> get(jlong id) {
    std::lock_guard<std::mutex> lock(registryMutex);
    auto it = sessions.find(id);
    if (it == sessions.end()) throw std::runtime_error("Session is closed");
    return it->second;
}
void fail(JNIEnv *env, const std::exception &error) {
    if (!env->ExceptionCheck()) env->ThrowNew(env->FindClass("java/lang/IllegalStateException"), error.what());
}
bool aborted(void *data) { if(phase==4||phase==5)++abortCallbacks;return static_cast<Session *>(data)->cancelled.load(); }
bool progress(float, void *data) { if(phase==2)++loadCallbacks;return !static_cast<Session *>(data)->cancelled.load(); }
std::string bytes(JNIEnv *env, jbyteArray value) {
    if (!value) throw std::runtime_error("Missing UTF-8 bytes");
    std::string result(env->GetArrayLength(value), '\0');
    env->GetByteArrayRegion(value, 0, result.size(), reinterpret_cast<jbyte *>(result.data()));
    return result;
}
}
extern "C" JNIEXPORT jstring JNICALL Java_org_pocketlore_app_NativeRuntime_identity(JNIEnv *env, jclass) {
    std::string identity="llama.cpp " POCKETLORE_REVISION "; CPU; context=2048; sequences=1; KV=f16; sessions=1; threads="+std::to_string(runtimeThreads())+"; model-budget="+std::to_string(pocketloreModelLimit)+"; greedy default; Qwen3 claims: non-thinking, t=0.7, k=20, p=0.8, presence=1.5/256, seed=42";
#if defined(POCKETLORE_HOST_SCREEN) && !defined(__ANDROID__)
    identity+="; HOST SCREEN native CPU ISA; not Android admission";
#endif
    return env->NewStringUTF(identity.c_str());
}
extern "C" JNIEXPORT jlong JNICALL Java_org_pocketlore_app_NativeRuntime_create(JNIEnv *env, jclass) {
    try {
        std::call_once(backendOnce, [] { llama_backend_init(); });
        std::lock_guard<std::mutex> lock(registryMutex);
        if (residentCount.load() != 0) throw std::runtime_error("One native session at a time; wait for cancellation and release");
        jlong id = nextId++;
        auto session = std::make_shared<Session>();
        sessions.emplace(id, session);
        return id;
    } catch (const std::exception &e) { fail(env, e); return 0; }
}
extern "C" JNIEXPORT void JNICALL Java_org_pocketlore_app_NativeRuntime_load(JNIEnv *env, jclass, jlong id, jbyteArray path) {
    try {
        auto s = get(id);
        std::lock_guard<std::mutex> lock(s->operation);
        if (s->cancelled) throw std::runtime_error("Cancelled");
        if (s->model) throw std::runtime_error("Model already loaded");
        auto p = llama_model_default_params();
        p.n_gpu_layers = 0;
        p.progress_callback = progress;
        p.progress_callback_user_data = s.get();
        const auto filename = bytes(env, path);
        if (filename.find('\0') != std::string::npos) throw std::runtime_error("Invalid model path");
        struct stat fileInfo{};
        if (stat(filename.c_str(), &fileInfo) != 0 || !S_ISREG(fileInfo.st_mode) || fileInfo.st_size < 4 || static_cast<uint64_t>(fileInfo.st_size) > pocketloreModelLimit) throw std::runtime_error("Model file must be regular and within the compiled admission limit");
        PhaseScope observation(1);
        // The pinned upstream no_alloc model propagates simulated allocation into its context.
        // Metadata/graph bookkeeping still allocates; this is not protection from all OOMs.
        auto dryParams=p;dryParams.no_alloc=true;dryParams.load_mode=LLAMA_LOAD_MODE_NONE;
        using Model=std::unique_ptr<llama_model,decltype(&llama_model_free)>;
        using DryContext=std::unique_ptr<llama_context,decltype(&llama_free)>;
        {
            Model dry(llama_model_load_from_file(filename.c_str(),dryParams),llama_model_free);
            if(!dry)throw std::runtime_error(s->cancelled ? "Cancelled" : "Cannot preflight GGUF model");
            if(s->cancelled)throw std::runtime_error("Cancelled");
            auto cp=contextParams();cp.abort_callback=aborted;cp.abort_callback_data=s.get();
            DryContext simulated(llama_init_from_model(dry.get(),cp),llama_free);
            if(!simulated)throw std::runtime_error("Cannot estimate inference buffers");
            uint64_t model=0,kv=0,compute=0;
            for(const auto &entry:llama_get_memory_breakdown(simulated.get())){model+=entry.second.model;kv+=entry.second.context;compute+=entry.second.compute;}
            estimatedModel=model;estimatedKV=kv;estimatedCompute=compute;
            requireNativeBudget(model,kv,compute);
        }
        if(s->cancelled)throw std::runtime_error("Cancelled");
        phase=2;
        s->model = llama_model_load_from_file(filename.c_str(), p);
        if(s->cancelled){if(s->model){llama_model_free(s->model);s->model=nullptr;}throw std::runtime_error("Cancelled");}
        if (!s->model) throw std::runtime_error(s->cancelled ? "Cancelled" : "Cannot load GGUF model");
        if (llama_model_has_encoder(s->model)) {
            llama_model_free(s->model); s->model = nullptr;
            throw std::runtime_error("Only decoder models are supported");
        }
    } catch (const std::exception &e) { fail(env, e); }
}
static std::string chatText(JNIEnv *env, const std::shared_ptr<Session>& s, jbyteArray system, jbyteArray prompt) {
    auto text=bytes(env,prompt);
    if(text.size()>32768)throw std::runtime_error("Prompt exceeds byte limit");
            if (text.find('\0') != std::string::npos || text.find("<|") != std::string::npos || text.find("[INST]") != std::string::npos)
                throw std::runtime_error("Unsupported prompt control marker");
            const char *tmpl = llama_model_chat_template(s->model, nullptr);
            if (!tmpl) throw std::runtime_error("Model has no supported chat template");
            std::string instruction = bytes(env, system);
            if (instruction.size() > 4096 || instruction.find('\0') != std::string::npos)
                throw std::runtime_error("Invalid system instruction");
            llama_chat_message messages[] = {{"system", instruction.c_str()}, {"user", text.c_str()}};
            int size = llama_chat_apply_template(tmpl, messages, 2, true, nullptr, 0);
            if (size <= 0 || size > 65536) throw std::runtime_error("Unsupported or oversized chat template");
            std::vector<char> formatted(size);
            if (llama_chat_apply_template(tmpl, messages, 2, true, formatted.data(), size) != size)
                throw std::runtime_error("Chat formatting failed");
            text.assign(formatted.data(), size);
            char architecture[64]={};
            llama_model_meta_val_str(s->model,"general.architecture",architecture,sizeof(architecture));
            if(std::string(architecture)=="qwen3") {
                // Upstream Qwen3 enable_thinking=false assistant prefix. No reasoning tokens are generated.
                const std::string assistant="<|im_start|>assistant\n";
                if(text.size()<assistant.size() || text.compare(text.size()-assistant.size(),assistant.size(),assistant)!=0 || std::string(tmpl).find("enable_thinking")==std::string::npos)
                    throw std::runtime_error("Unsupported Qwen3 non-thinking template");
                text+="<think>\n\n</think>\n\n";
            }
    return text;
}
extern "C" JNIEXPORT jint JNICALL Java_org_pocketlore_app_NativeRuntime_countChatTokens(JNIEnv *env,jclass,jlong id,jbyteArray system,jbyteArray prompt) {
    try {
        auto s=get(id);std::lock_guard<std::mutex> lock(s->operation);
        if(!s->model)throw std::runtime_error("No model loaded");
        auto text=chatText(env,s,system,prompt);
        return -llama_tokenize(llama_model_get_vocab(s->model),text.data(),text.size(),nullptr,0,true,true);
    } catch(const std::exception& e){fail(env,e);return 0;}
}
static jint generate(JNIEnv *env, jlong id, jbyteArray prompt, jint limit, jobject sink, bool chat, jbyteArray system = nullptr, int sources = 0, bool combined = false) {
    try {
        auto s = get(id);
        std::lock_guard<std::mutex> lock(s->operation);
        if (!s->model) throw std::runtime_error("No model loaded");
        if (limit < 1 || limit > 256 || !sink) throw std::runtime_error("Invalid generation arguments");
        if (s->cancelled) return -1;
        auto text = bytes(env, prompt);
        if (text.size() > 32768) throw std::runtime_error("Prompt exceeds byte limit");
        if (chat) text=chatText(env,s,system,prompt);
        const auto *vocab = llama_model_get_vocab(s->model);
        int count = -llama_tokenize(vocab, text.data(), text.size(), nullptr, 0, true, chat);
        if (count <= 0 || count + limit > 2048) throw std::runtime_error("Prompt and output exceed 2048-token context");
        std::vector<llama_token> tokens(count);
        if (llama_tokenize(vocab, text.data(), text.size(), tokens.data(), count, true, chat) != count)
            throw std::runtime_error("Tokenization failed");
        PhaseScope observation(3);promptTokens=count;
        requireNativeBudget(estimatedModel,estimatedKV,estimatedCompute);
        auto params = contextParams();
        params.abort_callback = aborted; params.abort_callback_data = s.get();
        using Context = std::unique_ptr<llama_context, decltype(&releaseContext)>;
        ++contextAttempts;
        Context ctx(llama_init_from_model(s->model, params), releaseContext);
        if (!ctx){++allocationFailures;throw std::runtime_error("Cannot create inference context");}
        ++activeContexts;
        uint64_t modelBytes=0,kvBytes=0,workBytes=0;
        for(const auto &entry:llama_get_memory_breakdown(ctx.get())){modelBytes+=entry.second.model;kvBytes+=entry.second.context;workBytes+=entry.second.compute;}
        modelBufferBytes=modelBytes;contextBytes=kvBytes;computeBytes=workBytes;
        // Retain actual accounting as a second screen after simulated preflight.
        requireNativeBudget(modelBytes,kvBytes,workBytes);
        using Sampler = std::unique_ptr<llama_sampler, decltype(&llama_sampler_free)>;
        Sampler sampler(nullptr,llama_sampler_free);
        if(sources>0) {
            if(sources>4)throw std::runtime_error("Too many synthesis sources");
            // Total output tokens, not a character counter, bound claim length.
            // A second claim is optional even for a comparison; never force filler.
            std::string grammar="root ::= \"Insufficient evidence.\" | claim (\"\\n\" claim){0,3}\n";
            grammar+=R"(claim ::= references " " [^\n\r\[\].]+ "."
references ::= )";
            if(combined) {
                grammar+="\"";for(int i=1;i<=sources;i++){if(i>1)grammar+=" ";grammar+="[S"+std::to_string(i)+"]";}grammar+="\"\n";
            } else grammar+="citation (\" \" citation)?\n";
            grammar+="citation ::= ";
            for(int i=1;i<=sources;i++){if(i>1)grammar+=" | ";grammar+="\"[S"+std::to_string(i)+"]\"";}
            grammar+="\n";
            auto *constraint=llama_sampler_init_grammar(vocab,grammar.c_str(),"root");
            if(!constraint)throw std::runtime_error("Cannot initialize claim grammar");
            sampler.reset(llama_sampler_chain_init(llama_sampler_chain_default_params()));
            if(!sampler){llama_sampler_free(constraint);throw std::runtime_error("Cannot initialize sampler chain");}
            llama_sampler_chain_add(sampler.get(),constraint);
            char architecture[64]={};
            llama_model_meta_val_str(s->model,"general.architecture",architecture,sizeof(architecture));
            if(std::string(architecture)=="qwen3") {
                // Upstream non-thinking sampling guidance; fixed seed makes this development run reproducible.
                llama_sampler_chain_add(sampler.get(),llama_sampler_init_penalties(llama_vocab_n_tokens(vocab),256,1.0f,0.0f,1.5f));
                llama_sampler_chain_add(sampler.get(),llama_sampler_init_top_k(20));
                llama_sampler_chain_add(sampler.get(),llama_sampler_init_top_p(0.8f,1));
                llama_sampler_chain_add(sampler.get(),llama_sampler_init_temp(0.7f));
                llama_sampler_chain_add(sampler.get(),llama_sampler_init_dist(42));
            } else llama_sampler_chain_add(sampler.get(),llama_sampler_init_greedy());
        } else sampler.reset(llama_sampler_init_greedy());
        if (!sampler) throw std::runtime_error("Cannot create sampler");
        jclass sinkClass = env->GetObjectClass(sink);
        jmethodID emit = env->GetMethodID(sinkClass, "onToken", "([B)V");
        env->DeleteLocalRef(sinkClass);
        if (!emit) return 0;
        auto batch = llama_batch_get_one(tokens.data(), count);
        llama_token token = 0;
        int generated = 0;
        while (generated < limit) {
            if (s->cancelled) return -1;
            phase=generated==0 ? 4 : 5;
            int result = llama_decode(ctx.get(), batch);
            if (s->cancelled) return -1;
            if (result != 0) throw std::runtime_error("Model decode failed");
            token = llama_sampler_sample(sampler.get(), ctx.get(), -1);
            if (llama_vocab_is_eog(vocab, token)) break;
            int n = llama_token_to_piece(vocab, token, nullptr, 0, 0, false);
            if (n < 0) n = -n;
            std::vector<char> piece(n);
            if (llama_token_to_piece(vocab, token, piece.data(), n, 0, false) != n)
                throw std::runtime_error("Token decoding failed");
            jbyteArray data = env->NewByteArray(n);
            if (!data) return 0;
            env->SetByteArrayRegion(data, 0, n, reinterpret_cast<const jbyte *>(piece.data()));
            env->CallVoidMethod(sink, emit, data);
            env->DeleteLocalRef(data);
            if (env->ExceptionCheck()) return 0;
            ++generated;
            batch = llama_batch_get_one(&token, 1);
        }
        return s->cancelled ? -1 : generated;
    } catch (const std::exception &e) { fail(env, e); return 0; }
}
extern "C" JNIEXPORT jint JNICALL Java_org_pocketlore_app_NativeRuntime_generate(JNIEnv *env, jclass, jlong id, jbyteArray prompt, jint limit, jobject sink) {
    return generate(env, id, prompt, limit, sink, false);
}
extern "C" JNIEXPORT jint JNICALL Java_org_pocketlore_app_NativeRuntime_generateChat(JNIEnv *env, jclass, jlong id, jbyteArray system, jbyteArray prompt, jint limit, jobject sink) {
    return generate(env, id, prompt, limit, sink, true, system);
}
extern "C" JNIEXPORT jint JNICALL Java_org_pocketlore_app_NativeRuntime_generateClaims(JNIEnv *env,jclass,jlong id,jbyteArray system,jbyteArray prompt,jint limit,jobject sink,jint sources,jboolean combined) {
    if(sources<1 || sources>4){std::runtime_error error("Invalid claim source count");fail(env,error);return 0;}
    return generate(env,id,prompt,limit,sink,true,system,sources,combined);
}
extern "C" JNIEXPORT void JNICALL Java_org_pocketlore_app_NativeRuntime_cancel(JNIEnv *env, jclass, jlong id) {
    try { get(id)->cancelled = true; } catch (const std::exception &e) { fail(env, e); }
}
extern "C" JNIEXPORT void JNICALL Java_org_pocketlore_app_NativeRuntime_reset(JNIEnv *env, jclass, jlong id) {
    try {
        auto s = get(id);
        std::unique_lock<std::mutex> lock(s->operation, std::try_to_lock);
        if (!lock.owns_lock()) throw std::runtime_error("Session is busy");
        s->cancelled = false;
    } catch (const std::exception &e) { fail(env, e); }
}
extern "C" JNIEXPORT void JNICALL Java_org_pocketlore_app_NativeRuntime_close(JNIEnv *, jclass, jlong id) {
    std::shared_ptr<Session> s;
    {
        std::lock_guard<std::mutex> lock(registryMutex);
        auto it = sessions.find(id);
        if (it == sessions.end()) return;
        s = it->second; sessions.erase(it);
    }
    s->cancelled = true; // An in-flight call retains ownership until it exits.
}

extern "C" JNIEXPORT jlongArray JNICALL Java_org_pocketlore_app_NativeRuntime_resourceState(JNIEnv *env,jclass) {
    std::lock_guard<std::mutex> lock(registryMutex);
    jlong values[]={static_cast<jlong>(residentCount.load()),activeContexts.load(),static_cast<jlong>(modelBufferBytes.load()),static_cast<jlong>(contextBytes.load()),static_cast<jlong>(computeBytes.load())};
    auto result=env->NewLongArray(5);if(result)env->SetLongArrayRegion(result,0,5,values);return result;
}

extern "C" JNIEXPORT jlongArray JNICALL Java_org_pocketlore_app_NativeRuntime_operationState(JNIEnv *env,jclass) {
    jlong values[]={phase.load(),static_cast<jlong>(loadCallbacks.load()),static_cast<jlong>(abortCallbacks.load()),static_cast<jlong>(promptTokens.load()),static_cast<jlong>(contextAttempts.load()),static_cast<jlong>(allocationFailures.load()),static_cast<jlong>(estimatedModel.load()),static_cast<jlong>(estimatedKV.load()),static_cast<jlong>(estimatedCompute.load())};
    auto result=env->NewLongArray(9);if(result)env->SetLongArrayRegion(result,0,9,values);return result;
}
