"""Accept the supplied aggregate review only for its exact immutable development evidence."""
import hashlib,json,pathlib
REVIEW_SHA256='12b6a7842a0cdde5959d72d0540802f0c1297895f5eff03acbbac5cf3fbedf86'
CHECKPOINT='65dd1bb376ddbdf7136572036efd4bc0fd0bbe93'

def validate_review(root,review_bytes,overrides=None):
    if review_bytes is None or hashlib.sha256(review_bytes).hexdigest()!=REVIEW_SHA256:
        raise ValueError('Missing or changed supplied independent review')
    review=json.loads(review_bytes)
    if review['checkpoint']!=CHECKPOINT:raise ValueError('Wrong reviewed checkpoint')
    # Raw rework is preserved: semantic support does not convert the old failed check to a pass.
    assert review['raw_critic']['decision']=='rework'
    assert review['interpretation']['minimum_useful_original_briefs']>=12
    assert review['interpretation']['per_case_independent_labels_available'] is False
    overrides=overrides or {}
    for name,expected in review['reviewed_files'].items():
        actual=overrides[name] if name in overrides else (root/name).read_bytes()
        if actual is None or hashlib.sha256(actual).hexdigest()!=expected:
            raise ValueError('Review no longer applies to: '+name)
    return review

def regressions(root,review_bytes):
    rejected=0
    def reject(data,overrides=None):
        nonlocal rejected
        try:validate_review(root,data,overrides)
        except ValueError:rejected+=1
        else:raise AssertionError('Changed review/evidence accepted')
    reject(None);reject(review_bytes+b'changed')
    review=json.loads(review_bytes)
    for field,value in [('checkpoint','0'*40),('interpretation',{'minimum_useful_original_briefs':1})]:
        altered=dict(review);altered[field]=value;reject(json.dumps(altered).encode())
    for name in ['docs/evidence/research-brief/availability/outputs.json','tools/evaluation/research-brief/sources.json','android/app/src/main/java/org/pocketlore/app/EvidenceAvailability.java']:
        reject(review_bytes,{name:None});reject(review_bytes,{name:(root/name).read_bytes()+b'changed'})
    return rejected
