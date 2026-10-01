#include <jni.h>
#include "llama.h"
#include <atomic>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace {
struct Session {
    std::atomic<bool> cancelled{false};
    std::mutex operation;
    llama_model *model = nullptr;
    ~Session() { if (model) llama_model_free(model); }
};
std::mutex registryMutex;
std::unordered_map<jlong, std::shared_ptr<Session>> sessions;
jlong nextId = 1;
std::once_flag backendOnce;
std::shared_ptr<Session> get(jlong id) {
    std::lock_guard<std::mutex> lock(registryMutex);
    auto it = sessions.find(id);
    if (it == sessions.end()) throw std::runtime_error("Session is closed");
    return it->second;
}
void fail(JNIEnv *env, const std::exception &error) {
    if (!env->ExceptionCheck()) env->ThrowNew(env->FindClass("java/lang/IllegalStateException"), error.what());
}
bool aborted(void *data) { return static_cast<Session *>(data)->cancelled.load(); }
bool progress(float, void *data) { return !aborted(data); }
std::string bytes(JNIEnv *env, jbyteArray value) {
    if (!value) throw std::runtime_error("Missing UTF-8 bytes");
    std::string result(env->GetArrayLength(value), '\0');
    env->GetByteArrayRegion(value, 0, result.size(), reinterpret_cast<jbyte *>(result.data()));
    return result;
}
}
extern "C" JNIEXPORT jstring JNICALL Java_org_pocketlore_app_NativeRuntime_identity(JNIEnv *env, jclass) {
    return env->NewStringUTF("llama.cpp " POCKETLORE_REVISION "; CPU; context=2048; threads=2; greedy");
}
extern "C" JNIEXPORT jlong JNICALL Java_org_pocketlore_app_NativeRuntime_create(JNIEnv *env, jclass) {
    try {
        std::call_once(backendOnce, [] { llama_backend_init(); });
        std::lock_guard<std::mutex> lock(registryMutex);
        jlong id = nextId++;
        sessions.emplace(id, std::make_shared<Session>());
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
        s->model = llama_model_load_from_file(filename.c_str(), p);
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
        auto params = llama_context_default_params();
        params.n_ctx = 2048; params.n_batch = 2048; params.n_ubatch = 128;
        params.n_threads = 2; params.n_threads_batch = 2;
        params.abort_callback = aborted; params.abort_callback_data = s.get();
        using Context = std::unique_ptr<llama_context, decltype(&llama_free)>;
        Context ctx(llama_init_from_model(s->model, params), llama_free);
        if (!ctx) throw std::runtime_error("Cannot create inference context");
        using Sampler = std::unique_ptr<llama_sampler, decltype(&llama_sampler_free)>;
        Sampler sampler(nullptr,llama_sampler_free);
        if(sources>0) {
            if(sources>4)throw std::runtime_error("Too many synthesis sources");
            std::string grammar=R"(root ::= "Insufficient evidence." | claim ("\n" claim)?
claim ::= references " " [^\n\r\[\].]{1,220} "."
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
            llama_sampler_chain_add(sampler.get(),llama_sampler_init_greedy());
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
