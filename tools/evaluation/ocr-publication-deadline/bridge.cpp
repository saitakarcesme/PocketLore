#include <jni.h>
#include "ocr_deadline.h"
extern "C" JNIEXPORT jlong JNICALL Java_org_pocketlore_app_DeadlineProbe_nativeRemaining(JNIEnv* e,jclass,jlong budget,jlong start,jlong tick,jboolean stop,jboolean millis){
 try{std::atomic<bool> cancel{bool(stop)};attachment_ocr::Deadline d(budget,cancel,start);return millis?d.milliseconds(tick):d.remaining(tick);}catch(const std::exception&){e->ThrowNew(e->FindClass("java/lang/IllegalArgumentException"),"Invalid OCR budget");return -1;}
}
