#include "text_transport.h"
#include <vector>
extern "C" JNIEXPORT jstring JNICALL Java_Transport_convert(JNIEnv* env, jclass, jbyteArray input, jint mode) {
    std::atomic<bool> cancel{mode == 4};
    if (mode == 3) return attachment_text::from_cstring(env, nullptr);
    if (mode == 5) {
        auto cls=env->FindClass("java/lang/IllegalStateException");
        env->ThrowNew(cls,"original pending exception"); env->DeleteLocalRef(cls);
        return attachment_text::from_utf8(env,"ok",2);
    }
    jsize n=env->GetArrayLength(input);
    if (n > 65537) { attachment_text::reject(env,"Harness input limit"); return nullptr; }
    std::vector<char> bytes(static_cast<size_t>(n)+1,0);
    env->GetByteArrayRegion(input,0,n,reinterpret_cast<jbyte*>(bytes.data()));
    if (env->ExceptionCheck()) return nullptr;
    if (mode == 1) return attachment_text::from_cstring(env,bytes.data());
    if (mode == 2) { if(n != 65536) {attachment_text::reject(env,"Invalid missing-terminator fixture"); return nullptr;} std::fill(bytes.begin(),bytes.end(),'x'); return attachment_text::from_cstring(env,bytes.data()); }
    return attachment_text::from_utf8(env,bytes.data(),n,&cancel);
}
