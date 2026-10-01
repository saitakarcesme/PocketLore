#include <jni.h>
#include <sqlite3.h>
#include <string>
#include <stdexcept>
#include <chrono>
#include <memory>
namespace {
struct Progress { JNIEnv* env; jobject cancel; jmethodID method; std::chrono::steady_clock::time_point start; };
int progress(void* arg){auto*p=static_cast<Progress*>(arg);if(p->env->CallBooleanMethod(p->cancel,p->method)||p->env->ExceptionCheck())return 1;return std::chrono::steady_clock::now()-p->start>std::chrono::seconds(15);}
std::string utf(JNIEnv* e,jstring s){if(!s)throw std::runtime_error("Missing query/path");const char*p=e->GetStringUTFChars(s,nullptr);if(!p)throw std::runtime_error("String allocation");std::string r(p);e->ReleaseStringUTFChars(s,p);return r;}
void quoted(std::string& out,const unsigned char* p,int length){out+='"';const char*hex="0123456789abcdef";for(int i=0;i<length;i++){unsigned c=p[i];if(c=='"'||c=='\\'){out+='\\';out+=char(c);}else if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=char(c);}out+='"';}
}
extern "C" JNIEXPORT jbyteArray JNICALL Java_org_pocketlore_app_NativeIndex_query(JNIEnv*e,jclass,jstring path,jstring sql,jobjectArray args,jint maxRows,jobject cancel){
 sqlite3* db=nullptr;sqlite3_stmt* statement=nullptr;jbyteArray result=nullptr;
 try{
  if(maxRows<1||maxRows>256||!cancel)throw std::runtime_error("Query admission");
  auto method=e->GetMethodID(e->FindClass("java/util/function/BooleanSupplier"),"getAsBoolean","()Z");Progress p{e,cancel,method,std::chrono::steady_clock::now()};if(progress(&p))throw std::runtime_error("Query cancelled");
  auto file=utf(e,path),query=utf(e,sql);if(query.size()>65536)throw std::runtime_error("SQL bound");
  sqlite3_hard_heap_limit64(64LL*1024*1024);
  if(sqlite3_open_v2(file.c_str(),&db,SQLITE_OPEN_READONLY|SQLITE_OPEN_NOMUTEX,nullptr)!=SQLITE_OK)throw std::runtime_error("Read-only index open failed");
  sqlite3_limit(db,SQLITE_LIMIT_LENGTH,1048576);sqlite3_limit(db,SQLITE_LIMIT_COLUMN,32);sqlite3_db_config(db,SQLITE_DBCONFIG_TRUSTED_SCHEMA,0,nullptr);sqlite3_exec(db,"PRAGMA cache_size=-4096;PRAGMA mmap_size=0;PRAGMA temp_store=MEMORY;PRAGMA query_only=ON",nullptr,nullptr,nullptr);sqlite3_progress_handler(db,1000,progress,&p);
  const char*tail=nullptr;if(sqlite3_prepare_v2(db,query.c_str(),-1,&statement,&tail)!=SQLITE_OK)throw std::runtime_error(sqlite3_errmsg(db));
  if(!statement||!sqlite3_stmt_readonly(statement))throw std::runtime_error("Read-only statements required");for(;tail&&*tail;tail++)if(*tail!=' '&&*tail!='\n'&&*tail!='\t')throw std::runtime_error("Multiple statements denied");
  int n=args?e->GetArrayLength(args):0;if(n!=sqlite3_bind_parameter_count(statement))throw std::runtime_error("Parameter count");
  for(int i=0;i<n;i++){jstring value=(jstring)e->GetObjectArrayElement(args,i);if(!value)sqlite3_bind_null(statement,i+1);else{const jchar*chars=e->GetStringChars(value,nullptr);int rc=sqlite3_bind_text16(statement,i+1,chars,e->GetStringLength(value)*2,SQLITE_TRANSIENT);e->ReleaseStringChars(value,chars);e->DeleteLocalRef(value);if(rc!=SQLITE_OK)throw std::runtime_error("Bind failed");}}
  std::string out="[";int rows=0,rc;while((rc=sqlite3_step(statement))==SQLITE_ROW){if(progress(&p))throw std::runtime_error("Query cancelled");if(++rows>maxRows)throw std::runtime_error("Row result bound; caller must LIMIT");if(rows>1)out+=',';out+='[';for(int c=0;c<sqlite3_column_count(statement);c++){if(c)out+=',';if(sqlite3_column_type(statement,c)==SQLITE_NULL)out+="null";else quoted(out,sqlite3_column_text(statement,c),sqlite3_column_bytes(statement,c));if(out.size()>2*1024*1024)throw std::runtime_error("Result byte bound");}out+=']';}if(rc!=SQLITE_DONE)throw std::runtime_error(sqlite3_errmsg(db));out+=']';result=e->NewByteArray(out.size());if(result)e->SetByteArrayRegion(result,0,out.size(),reinterpret_cast<const jbyte*>(out.data()));
 }catch(const std::exception&error){if(!e->ExceptionCheck())e->ThrowNew(e->FindClass("java/io/IOException"),error.what());}
 if(statement)sqlite3_finalize(statement);if(db)sqlite3_close(db);return result;
}
extern "C" JNIEXPORT jstring JNICALL Java_org_pocketlore_app_NativeIndex_identity(JNIEnv*e,jclass){return e->NewStringUTF(sqlite3_sourceid());}
