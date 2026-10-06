"""Deterministic, explicitly modified upstream identity for isolated archives."""
def apply(source, baseline, derivative):
    identity = baseline + '-pocketlore-' + derivative
    path = source / 'ggml/CMakeLists.txt'
    text = path.read_text()
    start = text.index('find_program(GIT_EXE')
    end = text.index('\nset(GGML_VERSION ', start)
    text = text[:start] + ('# Isolated modified archive: never discover an enclosing repository.\n'
        'set(GGML_BUILD_COMMIT "' + identity + '")\nset(GGML_GIT_DIRTY 0)\n') + text[end:]
    path.write_text(text)
    (source / 'cmake/build-info.cmake').write_text('''# Modified PocketLore archive; zero is not an upstream commit count.
set(BUILD_NUMBER 0)
set(BUILD_COMMIT "''' + identity + '''")
set(BUILD_COMPILER "${CMAKE_C_COMPILER_ID} ${CMAKE_C_COMPILER_VERSION}")
if(CMAKE_VS_PLATFORM_NAME)
 set(BUILD_TARGET "${CMAKE_VS_PLATFORM_NAME}")
else()
 set(BUILD_TARGET "${CMAKE_SYSTEM_NAME} ${CMAKE_SYSTEM_PROCESSOR}")
endif()
''')
    return identity
