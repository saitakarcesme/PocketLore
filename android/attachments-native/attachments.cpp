#include <jni.h>
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
static bool abort_ocr(void*,int){return cancelled.load();}
static void fail(JNIEnv* e,const char* s){e->ThrowNew(e->FindClass("java/io/IOException"),s);}
static std::string value(JNIEnv* e,jstring s){const char* p=e->GetStringUTFChars(s,nullptr);std::string r(p);e->ReleaseStringUTFChars(s,p);return r;}
extern "C" JNIEXPORT void JNICALL Java_org_pocketlore_app_AttachmentNative_reset(JNIEnv*,jclass){cancelled=false;}
extern "C" JNIEXPORT void JNICALL Java_org_pocketlore_app_AttachmentNative_cancel(JNIEnv*,jclass){cancelled=true;}
extern "C" JNIEXPORT jstring JNICALL Java_org_pocketlore_app_AttachmentNative_ocr(JNIEnv* e,jclass,jstring path,jbyteArray pixels,jint width,jint height){
 try{PhaseReset cleanup;phase=1;if(width<=0||height<=0||(int64_t)width*height>4000000||e->GetArrayLength(pixels)!=width*height){fail(e,"Image bounds rejected");return nullptr;}
 if(cancelled){fail(e,"Recognition cancelled");return nullptr;}tesseract::TessBaseAPI api;if(api.Init(value(e,path).c_str(),"eng",tesseract::OEM_LSTM_ONLY)!=0){fail(e,"English OCR data failed to load");return nullptr;}
 std::vector<unsigned char> image(width*height);e->GetByteArrayRegion(pixels,0,image.size(),reinterpret_cast<jbyte*>(image.data()));api.SetPageSegMode(tesseract::PSM_AUTO);api.SetImage(image.data(),width,height,1,width);api.SetSourceResolution(200);tesseract::ETEXT_DESC monitor;monitor.cancel=abort_ocr;monitor.set_deadline_msecs(30000);
 phase=3;if(cancelled||api.Recognize(&monitor)!=0||cancelled){fail(e,"OCR stopped or cancelled");return nullptr;}std::unique_ptr<char[]> text(api.GetUTF8Text());return e->NewStringUTF(text?text.get():"");
 }catch(const std::exception& ex){fail(e,ex.what());return nullptr;}
}
extern "C" JNIEXPORT jstring JNICALL Java_org_pocketlore_app_AttachmentNative_speech(JNIEnv* e,jclass,jstring path,jfloatArray audio){
 try{PhaseReset cleanup;phase=1;int n=e->GetArrayLength(audio);if(n<1600||n>240000){fail(e,"Audio must contain0.1–15 seconds");return nullptr;}if(cancelled){fail(e,"Recognition cancelled");return nullptr;}std::vector<float> pcm(n);e->GetFloatArrayRegion(audio,0,n,pcm.data());auto cp=whisper_context_default_params();cp.use_gpu=false;std::unique_ptr<whisper_context,decltype(&whisper_free)> ctx(whisper_init_from_file_with_params(value(e,path).c_str(),cp),whisper_free);if(!ctx){fail(e,"Local speech model failed to load");return nullptr;}
 auto p=whisper_full_default_params(WHISPER_SAMPLING_GREEDY);p.n_threads=2;p.translate=false;p.language="en";p.no_context=true;p.single_segment=true;p.max_tokens=64;p.temperature=0;p.temperature_inc=0;p.print_progress=false;p.print_realtime=false;p.print_timestamps=false;p.suppress_nst=true;p.no_speech_thold=0.6f;p.abort_callback=abort_job;p.encoder_begin_callback=[](whisper_context*,whisper_state*,void*){return !cancelled.load();};
 phase=2;if(cancelled||whisper_full(ctx.get(),p,pcm.data(),n)!=0||cancelled){fail(e,"Speech stopped or cancelled");return nullptr;}std::string text;for(int i=0;i<whisper_full_n_segments(ctx.get());i++)if(whisper_full_get_segment_no_speech_prob(ctx.get(),i)<0.6f)text+=whisper_full_get_segment_text(ctx.get(),i);return e->NewStringUTF(text.c_str());
 }catch(const std::exception& ex){fail(e,ex.what());return nullptr;}
}
