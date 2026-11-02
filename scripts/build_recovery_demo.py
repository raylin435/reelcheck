"""Build an inspectable, self-contained replay of recorded recovery attempts."""
import argparse
import html
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_recovery import consensus


def esc(value):return html.escape(str(value),quote=True)


def answer(value):
    if not value:return '<p>No valid final answer.</p>'
    quotes=''.join('<li><b>'+esc(c['passage_id'])+'</b>: '+esc(c['quote'])+'</li>' for c in value.get('citations',[]))
    return '<p class="verdict">'+esc(value.get('verdict','Unfinished draft'))+'</p><p>'+esc(value.get('explanation',''))+'</p><ul>'+quotes+'</ul>'


def card(task):
    verdict=consensus(task)
    status='Both judges accept' if verdict is True else 'Rejected or execution failed' if verdict is False else 'Judge disagreement / unresolved'
    title={'generic_retry':'Ordinary retry','targeted_recovery':'Targeted recovery','strong_reference':'DeepSeek reference'}[task['system']]
    costs=[c.get('cost_usd') for c in task['calls']]
    cost=f'${sum(costs):.5f}' if all(c is not None for c in costs) else 'Unknown'
    model='GLM 5.3 Flash' if task['model_role']=='cheap' else 'DeepSeek V4.1 Flash · high reasoning'
    failure={'truncated':'Stopped: response reached its token limit.','transport_error':'Stopped: API request timed out or failed in transit.','invalid_output':'Stopped: answer failed validation.','model_call_limit':'Stopped: model-call allowance exhausted.'}.get(task['status'],'')
    parts=['<article><h3>'+esc(title)+'</h3><p class="sub">'+esc(model)+'</p><p>'+esc(status)+'</p><p class="error">'+esc(failure)+'</p>',
           '<p>'+esc(task['searches'])+' searches · '+esc(task['reads'])+' reads · '+cost+' model estimate</p>',
           '<details><summary>Starting draft and detected errors</summary>'+answer(task['draft'])+'<p>'+esc(task['draft_status'])+'</p></details>']
    for g in task.get('recovery_gaps',[]):parts.append('<div class="gap"><b>Missing evidence identified by the model</b><p>'+esc(g['gap'])+'</p><p>Search: '+esc(g['query'])+'</p></div>')
    parts.extend(['<h4>Final answer</h4>',answer(task['output'])])
    if task.get('validation_errors'):parts.append('<p class="error">'+esc('; '.join(task['validation_errors']))+'</p>')
    parts.append('<details><summary>Every search and page read</summary><ol>')
    for e in task['tools']:
        req=e['request'];obs=e['observation'];label=esc(req.get('query',req.get('url')))
        if req['action']=='read':label='<a href="'+esc(req['url'])+'" target="_blank" rel="noopener noreferrer">'+label+'</a>'
        parts.append('<li><b>'+esc(req['action'])+'</b>: '+label+' <small>('+esc(obs['status'])+')</small></li>')
    parts.append('</ol></details><details><summary>Opened source links</summary><ul>')
    for e in task['evidence']:parts.append('<li>'+esc(e['id'])+': <a href="'+esc(e['url'])+'" target="_blank" rel="noopener noreferrer">'+esc(e['title'])+'</a></li>')
    parts.append('</ul></details><details><summary>Both evaluator explanations</summary>')
    for name,v in task.get('judge_votes',{}).items():parts.append('<h4>'+esc(name)+' · accepted='+esc(v['accepted'])+'</h4><p>'+esc((v.get('output') or {}).get('rationale',v.get('errors')))+'</p>')
    parts.append('</details></article>');return ''.join(parts)


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',required=True);args=p.parse_args()
    state=json.loads((Path(args.run)/'state.json').read_text())
    tasks=[t for t in state['tasks'] if t['phase']=='recovery']
    if not tasks or any(t['status']=='active' for t in tasks):raise ValueError('Finish the run before building its replay')
    cases=list(dict.fromkeys(t['case_id'] for t in tasks))
    if state.get('replay_only'):cases.sort()
    summary_path=Path(args.run)/'summary.json'
    if not summary_path.exists() and state.get('replay_only'):
        summary_path=Path(args.run).parent/'summary.json'
    scorecard=''
    if summary_path.exists():
        summary=json.loads(summary_path.read_text())
        rows=[]
        for arm,title in [('generic_retry','Ordinary retry'),('targeted_recovery','Targeted recovery'),('strong_reference','DeepSeek reference')]:
            stats=summary['systems'][arm]
            cost=stats['deployment_accounting']['estimated_cost_usd']
            rows.append('<tr><th>'+title+'</th><td>'+str(stats['accepted'])+'/'+str(stats['cases'])+'</td><td>'+str(stats['unresolved'])+'</td><td>'+str(stats['objective_failures'])+'</td><td>'+('Unknown' if cost is None else f'${cost:.5f}')+'</td></tr>')
        scorecard='<h2>All cases in this recorded run</h2><div style="overflow-x:auto"><table><thead><tr><th>Approach</th><th>Both judges accept</th><th>Unresolved</th><th>Execution failures</th><th>Model cost estimate</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div><p class="sub">Costs include the starting draft for each approach and exclude evaluator calls and web charges. Acceptance is machine agreement, not measured human accuracy.</p>'
    options=''.join('<option value="'+esc(cid)+'">'+esc(cid)+' — '+esc(next(t['claim']['claim_text'] for t in tasks if t['case_id']==cid))+'</option>' for cid in cases)
    sections=[]
    for i,cid in enumerate(cases):
        part=[t for t in tasks if t['case_id']==cid]
        by={t['system']:t for t in part}
        sections.append('<section data-case="'+esc(cid)+'"'+(' hidden' if i else '')+'><h2>'+esc(part[0]['claim']['claim_text'])+'</h2><div class="grid">'+''.join(card(by[a]) for a in ['generic_retry','targeted_recovery','strong_reference'])+'</div></section>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ReelCheck · Evidence recovery replay</title>
<style>
:root{color-scheme:light dark;font-family:system-ui,sans-serif;color:light-dark(#152333,#e3e9f0);background:light-dark(#f5f7fa,#121820)}
body{max-width:1320px;margin:32px auto;padding:0 20px}h1{margin-bottom:8px}h2{font-size:22px;margin:24px 0}h3{font-size:19px;margin:0}h4{margin-bottom:8px}p,li{line-height:1.55}a{color:light-dark(#1556a0,#8ac2ff);overflow-wrap:anywhere}.sub{opacity:.8}.notice{padding:14px 18px;background:light-dark(#e8eef6,#202c3b);border-radius:10px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}article{min-width:0;padding:20px;border:1px solid light-dark(#cbd5e1,#39465a);border-radius:12px;background:light-dark(#fff,#19222e)}select{display:block;width:100%;font:inherit;padding:10px;margin-top:8px}.verdict{font-weight:700;text-transform:uppercase}.gap{padding:12px;background:light-dark(#f1f4f9,#233144);border-radius:8px;margin:14px 0}details{border-top:1px solid light-dark(#dbe2eb,#39465a);padding:12px 0;margin-top:12px}summary{cursor:pointer}li{margin:8px 0}ul,ol{padding-left:22px}.error{color:light-dark(#a52424,#ffaaaa)}footer{margin-top:30px;font-size:13px;opacity:.8}[hidden]{display:none!important}@media(max-width:1000px){.grid{grid-template-columns:1fr}body{margin:20px auto}}
</style><h1>ReelCheck: evidence recovery</h1><p class="sub">Ordinary retry and targeted recovery share the same GLM draft and budget. DeepSeek researches separately.</p><p class="notice"><b>Recorded experiment replay — no live inference.</b> Machine assessments are fallible. Costs exclude unknown web-tool charges. A good example alone does not establish aggregate improvement.</p><div class="notice"><b>1. Claim</b> — a statement to check → <b>2. Search</b> — the model finds pages → <b>3. Evidence</b> — quotes from pages it reads → <b>4. Decision</b> — supported, contradicted, or not enough evidence.</div><p></p><label for="case">Choose a claim</label><select id="case">'''+options+'</select>'+''.join(sections)+'''<footer>Generated with Codex · Source queries, answers and judgments come from saved run traces.</footer><script>document.getElementById('case').addEventListener('change',function(){for(const s of document.querySelectorAll('[data-case]'))s.hidden=s.dataset.case!==this.value;});</script></html>'''
    page=page.replace('<label for="case">',scorecard+'<label for="case">')
    page=page.replace('</style>','table{width:100%;border-collapse:collapse;margin:14px 0;text-align:left}th,td{padding:12px;border-bottom:1px solid #98a6b744}thead th{font-size:13px}tbody th{font-weight:600}@media(max-width:600px){th,td{padding:8px 4px;font-size:12px}thead th{font-size:11px}}</style>')
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(page)
    print(json.dumps({'cases':len(cases),'cards':len(tasks),'out':str(out),'mode':'recorded_replay'}))


if __name__=='__main__':main()
