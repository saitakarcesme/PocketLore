#pragma once
#include <jni.h>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <new>
#include <vector>

// Ordinary UTF8, never JNI modified UTF8. Recognition allocations are separate.
namespace attachment_text {
constexpr size_t kMaxBytes = 65536;
constexpr size_t kMaxUnits = 65536;
inline void reject(JNIEnv* env, const char* message) {
    if (env->ExceptionCheck()) return;
    jclass type = env->FindClass("java/io/IOException");
    if (type) { env->ThrowNew(type, message); env->DeleteLocalRef(type); }
}
inline bool stopped(JNIEnv* env, const std::atomic<bool>* cancel) {
    if (env->ExceptionCheck()) return true;
    if (cancel && cancel->load()) { reject(env, "Recognition cancelled"); return true; }
    return false;
}
// Producer must supply readable C-string storage. At most cap+1 bytes examined.
inline bool cstring_length(JNIEnv* env, const char* data, size_t cap, size_t& size,
                           const std::atomic<bool>* cancel = nullptr) {
    if (stopped(env, cancel)) return false;
    if (!data || cap > kMaxBytes) { reject(env, "Invalid text producer"); return false; }
    for (size_t i = 0; i <= cap; ++i) {
        if ((i % 1024 == 0) && stopped(env, cancel)) return false;
        if (!data[i]) { size = i; return true; }
    }
    reject(env, "Text exceeds byte limit or lacks bounded terminator"); return false;
}
inline jstring from_utf8(JNIEnv* env, const char* data, size_t size,
                         const std::atomic<bool>* cancel = nullptr) {
    if (stopped(env, cancel)) return nullptr;
    if (!data || size > kMaxBytes) { reject(env, "Invalid text bytes or limit"); return nullptr; }
    try {
        std::vector<jchar> units;
        units.reserve(size); // <=128 KiB; output length never exceeds input bytes.
        for (size_t i = 0; i < size;) {
            if (stopped(env, cancel)) return nullptr;
            uint32_t cp = static_cast<unsigned char>(data[i++]);
            unsigned count = 0; uint32_t minimum = 0;
            if (cp < 0x80) {}
            else if (cp >= 0xc2 && cp <= 0xdf) { cp &= 31; count = 1; minimum = 0x80; }
            else if (cp >= 0xe0 && cp <= 0xef) { cp &= 15; count = 2; minimum = 0x800; }
            else if (cp >= 0xf0 && cp <= 0xf4) { cp &= 7; count = 3; minimum = 0x10000; }
            else { reject(env, "Invalid UTF8 lead byte"); return nullptr; }
            if (count > size - i) { reject(env, "Truncated UTF8"); return nullptr; }
            for (unsigned j = 0; j < count; ++j) {
                unsigned char byte = static_cast<unsigned char>(data[i++]);
                if ((byte & 0xc0) != 0x80) { reject(env, "Invalid UTF8 continuation"); return nullptr; }
                cp = (cp << 6) | (byte & 63);
            }
            if (cp < minimum || cp > 0x10ffff || (cp >= 0xd800 && cp <= 0xdfff)) {
                reject(env, "Invalid UTF8 scalar"); return nullptr;
            }
            if (units.size() + (cp > 0xffff ? 2 : 1) > kMaxUnits) {
                reject(env, "Text exceeds UTF16 limit"); return nullptr;
            }
            if (cp <= 0xffff) units.push_back(static_cast<jchar>(cp));
            else { cp -= 0x10000; units.push_back(static_cast<jchar>(0xd800 + (cp >> 10))); units.push_back(static_cast<jchar>(0xdc00 + (cp & 1023))); }
        }
        if (stopped(env, cancel)) return nullptr;
        const jchar empty = 0;
        return env->NewString(units.empty() ? &empty : units.data(), static_cast<jsize>(units.size()));
    } catch (const std::bad_alloc&) {
        reject(env, "Text allocation failed"); return nullptr;
    }
}
inline jstring from_cstring(JNIEnv* env, const char* data,
                            const std::atomic<bool>* cancel = nullptr) {
    size_t size = 0;
    return cstring_length(env, data, kMaxBytes, size, cancel) ? from_utf8(env, data, size, cancel) : nullptr;
}
}
