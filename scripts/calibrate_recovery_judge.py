"""Predeclared synthetic entailment checks; not a factual/source-quality benchmark."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reelcheck.providers import load_env,load_shell_exports
from reelcheck.recovery import judge_messages_v2
from reelcheck.research import assess_research_judgment
from recovery_batch import batch
from run_research import save


def fixtures():
    # Expected verdict and candidate acceptance are separated from every prompt.
    specs=[
      ('possibility_overclaim','The device has caused recorded fires.','The device could cause a fire.','supported','insufficient',False),
      ('occurrence_supported','The device has caused recorded fires.','Investigators recorded two fires caused by the device.','supported','supported',True),
      ('approximate_threshold','The measured share exceeded 90%.','The measured share was about 90%.','supported','insufficient',False),
      ('rounding_supported','Approximately 75% reported weekly use.','In the questionnaire, 74% reported weekly use.','supported','supported',True),
      ('context_date','In 2020, twelve cases were recorded.','2020 annual report. Results: twelve cases were recorded.','insufficient','supported',False),
      ('explicit_contradiction','All tested units passed inspection.','Of ten tested units, eight passed and two failed inspection.','contradicted','contradicted',True),
      ('risk_abstention','The device has caused recorded fires.','The device could cause a fire.','insufficient','insufficient',True),
      ('quantity_abstention','The measured share exceeded 90%.','The measured share was 93%.','insufficient','supported',False),
    ]
    cases=[]
    for name,claim,text,verdict,expected,accepted in specs:
        output={'claim_text':claim,'verdict':verdict,'citations':[{'passage_id':'R1','quote':text}],
                'uncertainty_reason':'missing_evidence' if verdict=='insufficient' else None,
                'explanation':('The evidence is inadequate.' if verdict=='insufficient' else 'The cited record establishes this verdict.')}
        task={'claim':{'claim_text':claim,'as_of':'2026-11-02'},'output':output,'tools':[],
              'evidence':[{'id':'R1','url':'https://fixture.example/record','resolved_url':'https://fixture.example/record',
                           'title':'Explicitly fictional test record','text':text,'retrieved_date':'2026-11-02','reader_may_return_partial_page':False}]}
        msgs=judge_messages_v2(task)
        msgs[0]['content']+='\nThis is a controlled fictional-language fixture. Treat the supplied fictional record as authoritative for its toy world. Assess literal entailment; source_suitability is true by construction. This does not test real-world source authority.\n'
        cases.append({'id':name,'task':task,'messages':msgs,'expected_verdict':expected,'expected_acceptance':accepted})
    return cases


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--live',action='store_true');args=p.parse_args()
    config=json.loads((ROOT/'config.research.json').read_text())
    judges=[('kimi',config['judge']),('deepseek',{**config['variants'][1],'parameters':{'reasoning_effort':'high'}})]
    cases=fixtures()
    tasks=[{'id':c['id']+'/'+name,'config':model,'messages':c['messages']} for c in cases for name,model in judges]
    if not args.live:
        print(json.dumps({'fixture_count':len(cases),'planned_calls':len(tasks),'live':False}));return
    load_env(ROOT/'.env');load_env(ROOT.parent/'.env');load_shell_exports(Path.home()/'.zshrc')
    rows=batch(tasks,args.out,3.)
    by={c['id']:c for c in cases};scores=[]
    for row in rows:
        name,judge=row['id'].split('/');case=by[name]
        assessment=assess_research_judgment(case['task'],row)
        value=row.get('output') or {}
        scores.append({'id':name,'judge':judge,'expected_verdict':case['expected_verdict'],
            'expected_acceptance':case['expected_acceptance'],'actual_verdict':value.get('expected_verdict'),
            'actual_acceptance':assessment['accepted'],'pass':not assessment['errors'] and
              value.get('expected_verdict')==case['expected_verdict'] and assessment['accepted']==case['expected_acceptance']})
    save(Path(args.out)/'calibration.json',{'fixtures':len(cases),'results':scores,
        'gate_passed':len(rows)==len(tasks) and all(s['pass'] for s in scores),
        'note':'Small synthetic logical sanity check; no human or real-world accuracy validation.'})
    print(json.dumps(scores,indent=2))


if __name__=='__main__':main()
