# Installed NDK compatibility source is built separately on this rig.
add_library(CpuFeatures::ndk_compat STATIC IMPORTED GLOBAL)
set_target_properties(CpuFeatures::ndk_compat PROPERTIES IMPORTED_LOCATION "${ATTACHMENT_CPU_FEATURES}" INTERFACE_INCLUDE_DIRECTORIES "${ANDROID_NDK}/sources/android/cpufeatures")
set(CpuFeaturesNdkCompat_FOUND TRUE)
