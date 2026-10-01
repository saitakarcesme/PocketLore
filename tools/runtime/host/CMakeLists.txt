cmake_minimum_required(VERSION 3.22)
project(pocketlore_host LANGUAGES C CXX)
find_package(JNI REQUIRED)
# Build the production bridge/controller dependencies unchanged. The Android
# project disables SIMD flags, so this host comparison uses that same CPU path.
include_directories(${JNI_INCLUDE_DIRS})
add_subdirectory("${PROJECT_ROOT}/android/app/src/main/cpp" production)
