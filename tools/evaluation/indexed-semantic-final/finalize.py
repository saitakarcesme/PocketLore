"""Explicit one-time evidence finalization, never invoked by mandatory checker."""
import sys
import core as C
R=C.R

def main(commit):
 destination=C.ROOT/'docs/evidence/indexed-semantic-final-review.json';C.need(not destination.exists() and not (C.BASE/'seal.json').exists(),'finalization-once')
 source=C.freeze(commit)
 files={str(p.relative_to(C.ROOT)):C.artifact(p) for p in sorted(C.RUN.rglob('*')) if p.is_file() or p.is_symlink()}
 # Delta is consumed through the newly frozen explicit finalization descriptor.
 e=R.consume(files[str((C.RUN/'delta.json').relative_to(C.ROOT))],True);C.need(e['source_commit']==commit and e['sources_before']==e['sources_after']==source and e['status']=='PASS','finalization-source')
 p={'format':'indexed-semantic-final-547','source_commit':e['source_commit'],'sources':source,'files':files,'initial_inventory_sha256':C.INITIAL,'old_tasks':{'543':'FAILED_STORAGE_CAP','544':'FAILED_REPLAY','545':'FAILED_PACKET_SOURCE','546':'FAILED_PIDFD_PREFIX_REVIEW'},'scope':'Fresh bounded synthetic delta and explicitly historical source replay only.'}
 C.save(destination,p);C.save(C.BASE/'seal.json',{'packet':R.descriptor(destination)})
if __name__=='__main__':main(sys.argv[1])
