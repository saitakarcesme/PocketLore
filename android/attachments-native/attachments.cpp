#include <jni.h>
#include "text_transport.h"
#include "ocr_deadline.h"
#include <tesseract/baseapi.h>
#include <tesseract/ocrclass.h>
#include <whisper.h>
#include <atomic>
#include <string>
#include <vector>
#include <memory>
static std::atomic<bool> cancelled{false};
static std::atomic<int> phase{0};
struct PhaseReset {~PhaseReset(){phase=0;}};
extern "C" JNIEXPORT jint JNICALL Java_org_pocketlore_app_AttachmentNative_phase(JNIEnv*,jclass){return phase.load();}
static bool abort_job(void*){return cancelled.load();}
static bool abort_ocr(void* opaque,int){return static_cast<attachment_ocr::Deadline*>(opaque)->stopped();}
static void fail(JNIEnv* e,const char* s){e->ThrowNew(e->FindClass("java/io/IOException"),s);}
static std::string value(JNIEnv* e,jstring s){const char* p=e->GetStringUTFChars(s,nullptr);std::string r(p);e->ReleaseStringUTFChars(s,p);return r;}
extern "C" JNIEXPORT void JNICALL Java_org_pocketlore_app_AttachmentNative_reset(JNIEnv*,jclass){cancelled=false;}
extern "C" JNIEXPORT void JNICALL Java_org_pocketlore_app_AttachmentNative_cancel(JNIEnv*,jclass){cancelled=true;}
extern "C" JNIEXPORT jstring JNICALL Java_org_pocketlore_app_AttachmentNative_ocr(JNIEnv* e,jclass,jstring path,jbyteArray pixels,jint width,jint height,jlong remainingNanos){
 try{PhaseReset cleanup;attachment_ocr::Deadline deadline(remainingNanos,cancelled);deadline.check();phase=1;
 if(!path||!pixels||width<=0||height<=0||(int64_t)width*height>4000000||e->GetArrayLength(pixels)!=width*height){attachment_text::reject(e,"Image bounds rejected");return nullptr;}
 const char* chars=e->GetStringUTFChars(path,nullptr);if(!chars)return nullptr;std::string directory;try{directory=chars;}catch(...){e->ReleaseStringUTFChars(path,chars);throw;}e->ReleaseStringUTFChars(path,chars);if(e->ExceptionCheck())return nullptr;
 deadline.check();tesseract::TessBaseAPI api;int initialized=api.Init(directory.c_str(),"eng",tesseract::OEM_LSTM_ONLY);deadline.check();if(initialized!=0){attachment_text::reject(e,"English OCR data failed to load");return nullptr;}
 std::vector<unsigned char> image(width*height);deadline.check();e->GetByteArrayRegion(pixels,0,image.size(),reinterpret_cast<jbyte*>(image.data()));if(e->ExceptionCheck())return nullptr;deadline.check();api.SetPageSegMode(tesseract::PSM_AUTO);api.SetImage(image.data(),width,height,1,width);api.SetSourceResolution(200);deadline.check();
 tesseract::ETEXT_DESC monitor;monitor.cancel=abort_ocr;monitor.cancel_this=&deadline;int milliseconds=deadline.milliseconds(attachment_ocr::now());if(milliseconds<=0)throw std::runtime_error("OCR remaining budget below one millisecond");monitor.set_deadline_msecs(milliseconds);
 phase=3;deadline.check();int recognized=api.Recognize(&monitor);deadline.check();if(recognized!=0){attachment_text::reject(e,"OCR stopped or cancelled");return nullptr;}
 std::unique_ptr<char[]> text(api.GetUTF8Text());deadline.check();jstring result=attachment_text::from_cstring(e,text.get(),&cancelled);if(e->ExceptionCheck())return nullptr;deadline.check();return result;
 }catch(const std::exception&){attachment_text::reject(e,"OCR stopped, cancelled or expired");return nullptr;}
}
extern "C" JNIEXPORT jstring JNICALL Java_org_pocketlore_app_AttachmentNative_speech(JNIEnv* e,jclass,jstring path,jfloatArray audio){
 try{PhaseReset cleanup;phase=1;int n=e->GetArrayLength(audio);if(n<1600||n>240000){fail(e,"Audio must contain 0.1 to 15 seconds");return nullptr;}if(cancelled){fail(e,"Recognition cancelled");return nullptr;}std::vector<float> pcm(n);e->GetFloatArrayRegion(audio,0,n,pcm.data());auto cp=whisper_context_default_params();cp.use_gpu=false;std::unique_ptr<whisper_context,decltype(&whisper_free)> ctx(whisper_init_from_file_with_params(value(e,path).c_str(),cp),whisper_free);if(!ctx){fail(e,"Local speech model failed to load");return nullptr;}
 auto p=whisper_full_default_params(WHISPER_SAMPLING_GREEDY);p.n_threads=2;p.translate=false;p.language="en";p.no_context=true;p.single_segment=true;p.max_tokens=64;p.temperature=0;p.temperature_inc=0;p.print_progress=false;p.print_realtime=false;p.print_timestamps=false;p.suppress_nst=true;p.no_speech_thold=0.6f;p.abort_callback=abort_job;p.encoder_begin_callback=[](whisper_context*,whisper_state*,void*){return !cancelled.load();};
 phase=2;if(cancelled||whisper_full(ctx.get(),p,pcm.data(),n)!=0||cancelled){fail(e,"Speech stopped or cancelled");return nullptr;}std::string text;for(int i=0;i<whisper_full_n_segments(ctx.get());i++)if(whisper_full_get_segment_no_speech_prob(ctx.get(),i)<0.6f){const char* segment=whisper_full_get_segment_text(ctx.get(),i);size_t bytes=0;if(!attachment_text::cstring_length(e,segment,attachment_text::kMaxBytes-text.size(),bytes,&cancelled))return nullptr;text.append(segment,bytes);}return attachment_text::from_utf8(e,text.data(),text.size(),&cancelled);
 }catch(const std::exception& ex){attachment_text::reject(e,"Native recognition exception");return nullptr;}
}
