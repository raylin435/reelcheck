"""Regrade the previously disputed real answer; preserve historical judgments."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reelcheck.recovery import judge_messages_v2
from reelcheck.research import assess_research_judgment
from reelcheck.providers import load_env,load_shell_exports
from recovery_batch import batch
from run_research import save

def main():
    load_env(ROOT/'.env');load_env(ROOT.parent/'.env');load_shell_exports(Path.home()/'.zshrc')
    state=json.loads((ROOT/'results/research-pilot-01/state.json').read_text())
    target=next(t for t in state['tasks'] if t['case_id']=='sf_02' and t['system']=='glm_direct')
    config=json.loads((ROOT/'config.recovery.json').read_text())
    jobs=[{'id':name,'config':model,'messages':judge_messages_v2(target)} for name,model in config['judges'].items()]
    out=ROOT/'results/recovery-disputed-audit-01'
    rows=batch(jobs,out,1.)
    assessments=[{'judge':r['id'],**assess_research_judgment(target,r),'output':r.get('output')} for r in rows]
    save(out/'audit.json',{'source':'research-pilot-01 sf_02 glm_direct','assessments':assessments,
                         'historical_result_unchanged':True})
    print(json.dumps(assessments,indent=2))

if __name__=='__main__':main()
