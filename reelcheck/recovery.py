"""Frozen research-recovery treatment and stricter, independently tested rubric."""
from copy import deepcopy
import json

from .contract import validate
from .research import SYSTEM, RESEARCH_JUDGE, apply_action, research_judge_messages

QUALIFIERS = '''
Distinguish a possibility from an observed occurrence: contaminated products or a
risk of positive tests do not establish that an actual person tested positive.
Approximate quantities do not establish a strict threshold. Conversely, do not
demand exact words when a faithful paraphrase or reasonable rounding is enough.
Use source headings, surrounding text and dates, not just the quoted sentence.
Do not claim a study is the latest, or that no contrary evidence exists, merely
because a limited search found no newer source. Search snippets remain uncitable
and cannot support extra factual assertions in your explanation.
'''
BASE_SYSTEM = SYSTEM + QUALIFIERS
GENERIC_RECOVERY = '''
You have one bounded ordinary review/retry opportunity. Reconsider your draft,
the opened evidence, and any execution/quotation errors. Correct mistakes and
return the best justified answer. You may use the remaining search/read budget
to improve the answer. You may retain a valid draft if no change is warranted.
This is not evaluator feedback: no reference answer or correctness label is given.
'''
TARGETED_RECOVERY = '''
You have one bounded targeted evidence-recovery opportunity. Inspect the draft
against the actually opened pages. Identify the most consequential unmet evidence
requirement (entity, quantity, scope, date, modality, causality or source quality).
If a page was blocked or empty, seek another source for that same requirement.
If research is needed, search for evidence that would resolve the specific gap,
including counterevidence. Every search action in this recovery phase must be:
{"action":"search","gap":"specific fact missing from the opened sources",
 "query":"a targeted query that could establish or refute that fact"}.
The gap is your hypothesis, not a trusted fact or proof of a semantic error.
Read actions and final-answer format are unchanged. Fix exact quotations using
only opened text. If no material gap exists, return the valid draft; if the budget
cannot resolve a material gap, return insufficient with a precise explanation.
This is not evaluator feedback: no reference answer or correctness label is given.
'''
JUDGE_V2 = RESEARCH_JUDGE + '''
Additional adjudication rules, version research_semantics_v2:
1. Documented contamination, an ingredient's capability, or a risk warning does not
establish an observed person/event. For "documented positive drug tests", identify
an actual observed test or an explicit source statement that such tests occurred.
2. "About X" alone establishes neither >X nor <X. Approximate equality and faithful
rounding can support "approximately X"; do not turn uncertainty into contradiction.
3. A relevant date can appear in a heading or surrounding passage. Do not reject
support merely because the exact quoted sentence omits context supplied elsewhere.
4. Evaluate factual assertions in the explanation too. Claims such as "latest",
"no newer study", and "no contrary evidence exists" need evidence; a bounded search
alone cannot establish them. Snippets are not opened-page evidence.
5. Distinguish a justified bounded insufficient verdict from unnecessary abstention.
Do not reward a system merely for refusing all decisions. If interpretation is
materially ambiguous, return ambiguous/low confidence instead of forcing a winner.
Apply these rules identically to every anonymous candidate. Do not infer correctness
from prose confidence, a real URL, exact quote matching, or the presence of a checklist.
'''


def recovery_task(initial, arm):
    task = deepcopy(initial)
    task['origin_system'] = initial['system']
    task['system'] = arm
    task['phase'] = 'recovery'
    task['status'] = 'active'
    task['draft'] = deepcopy(initial.get('output') or initial.get('last_answer'))
    task['draft_status'] = initial['status']
    task['shared_call_indices'] = [c['call_index'] for c in initial['calls']]
    task['phase_start_model_calls'] = task['model_calls']
    task['limits'] = {'max_searches': task['searches']+1, 'max_reads': task['reads']+2,
                      'max_results':5, 'max_page_chars':16000,
                      'max_model_calls':task['model_calls']+5}
    task['messages'][0]['content'] = BASE_SYSTEM + (TARGETED_RECOVERY if arm=='targeted_recovery' else GENERIC_RECOVERY)
    task['messages'].append({'role':'user','content':json.dumps({
        'controller':'Begin the single recovery episode. Shared draft; no truth label.',
        'draft':task['draft'], 'draft_status':task['draft_status'],
        'objective_errors':initial.get('validation_errors',[])},ensure_ascii=False)})
    task['output']=None
    task.pop('completed_at',None)
    task.pop('validation_errors',None)
    task.pop('pending',None)
    task['recovery_gaps']=[]
    return task


def recover_action(task, action):
    if isinstance(action,dict) and action.get('action')=='finish':
        task['last_answer']=deepcopy(action.get('answer'))
    if task['system']=='targeted_recovery' and isinstance(action,dict) and action.get('action')=='search':
        if set(action)!={'action','gap','query'} or not isinstance(action['gap'],str) or not action['gap'].strip():
            raise ValueError('Targeted recovery requires a specific evidence gap with its query')
        task['recovery_gaps'].append({'gap':action['gap'],'query':action['query']})
        action={k:v for k,v in action.items() if k!='gap'}
    return apply_action(task,action,task['limits'])


def judge_messages_v2(task):
    messages=research_judge_messages(task)
    messages[0]['content']=JUDGE_V2
    return messages
