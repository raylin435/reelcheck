"""Export a portable machine-reviewed pilot manifest; preserve strict-track status."""
import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reelcheck.__main__ import digest, save_json
from reelcheck.evaluation import read_jsonl
from reelcheck.media import sha256
from reelcheck.references import load_references
from scripts.report_machine_eval import verify_audit_binding


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','references','audit','out'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--media-zip',help='Optional local archive; never uploaded')
    p.add_argument('--audit-inputs',help='Original audited inputs when only evidence was revised')
    args=p.parse_args()
    out=Path(args.out)
    if out.exists():raise ValueError('Fresh export directory required')
    if args.media_zip and Path(args.media_zip).exists():raise ValueError('Fresh media archive required')
    cases=read_jsonl(args.inputs)
    bundle,refs=load_references(args.references,cases)
    if bundle.get('review_track')!='machine_reviewed':raise ValueError('Machine track required')
    audit=Path(args.audit)
    am=json.loads((audit/'manifest.json').read_text())
    verify_audit_binding(am,cases,args.audit_inputs)
    fidelity={a['case_id']:a for r in read_jsonl(audit/'audits.jsonl') if r['execution_status']=='completed' for a in r['output']['claims']}
    collections=[('data/shortform_candidates.jsonl','data/media/pilot-01/collection.json'),
                 ('data/shortform_machine_candidates_01.jsonl','data/media/machine-pilot-01/collection.json'),
                 ('data/shortform_machine_candidates_02.jsonl','data/media/machine-pilot-02/collection.json')]
    available={}
    exclusions=[]
    for seed,collection in collections:
        seeds={c['clip_id']:c for c in read_jsonl(ROOT/seed)}
        report=json.loads((ROOT/collection).read_text())
        if report['manifest_sha256']!=sha256(ROOT/seed):raise ValueError('Acquisition seeds changed')
        for record in report['clips']:
            available[record['clip_id']]=(seeds[record['clip_id']],record,Path(collection).parent)
            if not record.get('media',{}).get('technical_short_form_pass'):
                exclusions.append({'clip_id':record['clip_id'],'status':record['status'],'media':record.get('media')})
    clips=[];assets=[]
    for cid in sorted({c['provenance']['clip_id'] for c in cases}):
        seed,record,root=available[cid]
        media=record['media']
        path=ROOT/root/cid
        if not media['technical_short_form_pass'] or not media['decode_ok'] or not seed['rights']['redistribution_allowed']:
            raise ValueError('Media eligibility failed')
        if sha256(path/'original.mp4')!=media['sha256']:raise ValueError('Original media changed')
        source=(path/'source.html').read_text()
        credit=re.search(r'<h3>Video by\s*<a[^>]*>(.*?)</a>',source,re.S)
        creator=html.unescape(re.sub('<[^>]+>','',credit[1])).strip() if credit else seed['creator_group']
        files=[]
        for name in ('original.mp4','publisher_captions.vtt','timeline.json','ffprobe.json','source.html'):
            f=path/name
            if f.exists():
                files.append({'path':f'{cid}/{name}','sha256':sha256(f),'bytes':f.stat().st_size})
                assets.append((f,f'{cid}/{name}'))
        claims=[]
        for c in cases:
            if c['provenance']['clip_id']!=cid:continue
            prov=c['provenance'];ref=refs[c['case_id']]
            if not 0<=prov['start_seconds']<prov['end_seconds']<=media['duration_seconds']:
                raise ValueError('Invalid claim timing')
            f=fidelity.get(c['case_id'])
            new=c['evaluation_partition']=='new_clip_validation'
            claims.append({'case_id':c['case_id'],'start_seconds':prov['start_seconds'],'end_seconds':prov['end_seconds'],
                'evaluation_partition':c['evaluation_partition'],'reference_status':ref['review_status'],
                'machine_claim_fidelity':f,'included_in_all_case_denominator':True,
                'eligible_for_reference_scoring':bool(ref['acceptable_verdicts']) and (not new or bool(f and f['fidelity']=='faithful')),
                'human_reviewed':False})
        clips.append({'clip_id':cid,'title':seed['title'],'source_url':seed['source_url'],
            'creator_credit':creator,'rights':seed['rights'],'direct_media_url':record['direct_media_url'],
            'captions_url':record.get('captions_url'),'media':media,'files':files,'claims':claims,
            'caption_issues':record.get('caption_issues',[]),'native_social_publication_verified':False,
            'strict_human_reviewed_benchmark_admitted':False})
    out.mkdir(parents=True)
    copies=[(Path(args.inputs),'inputs.jsonl'),(Path(args.references),'references.frozen.json'),
            (audit/'audits.jsonl','claim_fidelity.jsonl'),(ROOT/'config.machine_semantic.json','config.json'),
            (ROOT/'MACHINE_EVAL_PROTOCOL.md','PROTOCOL.md')]
    if args.audit_inputs:copies.append((Path(args.audit_inputs),'audited_inputs.jsonl'))
    copies.append((audit/'manifest.json','claim_fidelity_manifest.json'))
    for source,name in copies:shutil.copyfile(source,out/name)
    manifest={'schema_version':1,'created_at':datetime.now(timezone.utc).isoformat(),'track':'machine_reviewed_fixed_evidence_pilot',
        'human_reviewed':False,'inputs_sha256':digest(cases),'reference_file_sha256':sha256(args.references),
        'case_count':len(cases),'clip_count':len(clips),'clips':clips,'acquisition_exclusions':exclusions,
        'artifact_sha256':{name:sha256(out/name) for _,name in copies},
        'disclosure':'Fixed-evidence inference; captions and sample-frame fidelity checks, not full audiovisual fact checking. Native social publication unverified. No provider upload or public publication performed.'}
    save_json(out/'manifest.json',manifest)
    (out/'README.md').write_text('# ReelCheck machine-reviewed pilot\n\n'
        'This is a portable fixed-evidence pilot, not human-verified ground truth.\n'
        'Use inputs.jsonl for candidate models. Keep references.frozen.json and claim_fidelity.jsonl out of candidate prompts.\n'
        'The manifest links original media and captions, byte hashes, duration/dimensions, rights and timestamped claims.\n'
        'Media must pass SHA256 verification after download; do not silently accept changed files.\n'
        'The optional media ZIP uses clip_id/original.mp4 and includes publisher captions, timeline, ffprobe and source pages.\n'
        'Public-domain asset markings and creator credits are per clip; no government endorsement is implied.\n'
        'Keep metadata/code in git and large MP4s in a release asset or licensed media store. No upload was performed.\n'
        'Publisher captions can be wrong; see caption_issues and the claim-fidelity limitations.\n'
        'For multimodal ingestion, pass actual video to a supported API or timestamped sampled frames plus audio/transcript; a source URL alone does not guarantee model access.\n')
    if args.media_zip:
        with zipfile.ZipFile(args.media_zip,'x',compression=zipfile.ZIP_STORED) as archive:
            for source,name in assets:archive.write(source,name)
            archive.write(out/'manifest.json','manifest.json')
            archive.write(out/'README.md','README.md')
        save_json(out/'media_archive.json',{'file':Path(args.media_zip).name,'sha256':sha256(args.media_zip),'bytes':Path(args.media_zip).stat().st_size})
    print(json.dumps({'cases':len(cases),'clips':len(clips),'out':str(out),'media_zip':args.media_zip},indent=2))


if __name__=='__main__':main()
