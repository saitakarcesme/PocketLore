"""Content-addressed Linux/Android derivation; never edits the pinned checkout."""
import hashlib,json,pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[3]; here=pathlib.Path(__file__).parent
from build_identity import apply as apply_build_identity
from binding import derivation_inputs, canonical_key, validate_cache
inputs=derivation_inputs(R)
key=canonical_key(inputs)
out=R/'downloads/native-cache-build'/('source-'+key)
def edit(p,old,new):
 s=p.read_text();assert s.count(old)==1,(p,old);p.write_text(s.replace(old,new))
if not out.exists():
 subprocess.run([sys.executable,str(here/'derive.py'),str(out)],check=True,stdout=sys.stderr)
 s=out/'source'
 build_identity=apply_build_identity(s,inputs['pinned_git_commit']['revision'],key)
 for p in (here/'native').glob('*'): (s/'src'/p.name).write_bytes(p.read_bytes())
 with (s/'src/CMakeLists.txt').open('a') as f:f.write('\ntarget_sources(llama PRIVATE pocketlore-sha.c)\ntarget_include_directories(llama PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../vendor/hash)\n')
 p=s/'src/llama-mmap.cpp'
 edit(p,'#include "llama-mmap.h"','#include "llama-mmap.h"\n#include "pocketlore-owned.h"')
 edit(p,'    std::vector<std::pair<size_t, size_t>> mapped_fragments;','    std::vector<std::pair<size_t, size_t>> mapped_fragments;\n    std::shared_ptr<pocketlore_owned::File> owner;')
 edit(p,'        int flags = MAP_SHARED;', '''        owner = pocketlore_owned::active;
        size_t offset = 0;
        if (owner) {
            owner->verify_fd(fd);
            pocketlore_owned::require(!prefetch && !numa, "Owned mapping requires no prefetch/NUMA policy");
            fd = owner->fd();
            offset = pocketlore_owned::window_offset;
            if (pocketlore_owned::window_size) size = pocketlore_owned::window_size;
            owner->validate_range(size, offset);
        }
        int flags = MAP_SHARED;''')
 edit(p,'addr = mmap(NULL, file->size(), PROT_READ, flags, fd, 0);','addr = mmap(NULL, size, PROT_READ, flags, fd, offset);')
 edit(p,'        mapped_fragments.emplace_back(0, file->size());','''        mapped_fragments.emplace_back(0, size);
        if (owner) {
            try { owner->register_mapping(addr, size, offset); }
            catch (...) { munmap(addr, size); throw; }
        }''')
 edit(p,'        int page_size = sysconf(_SC_PAGESIZE);','''        // Diagnostic mappings retain the complete original virtual span. No missing
        // fragment can later be mistaken for an owned mapped page. No prefault.
        if (owner) return;
        int page_size = sysconf(_SC_PAGESIZE);''')
 edit(p,'    ~impl() {\n        for (const auto & frag : mapped_fragments)', '    ~impl() {\n        if (owner) { owner->retire(addr); return; }\n        for (const auto & frag : mapped_fragments)')
 files={str(p.relative_to(s)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(s.rglob('*')) if p.is_file()}
 (out/'native-manifest.json').write_text(json.dumps({'input_sha256':key,'inputs':inputs,'files':files,'modified_build_identity':build_identity},sort_keys=True,indent=2))
validate_cache(out,inputs)
print(out/'source')
