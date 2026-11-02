"""A second GPT-OSS pass checks evidence requirements; no labels or oracle routing."""
from copy import deepcopy
import json

from .prompts import COMMON, MAP, public_input
from .structured import quote_output_schema

SEMANTIC_CHECK = '''Audit the previous draft, which may be wrong. Re-evaluate from the
original claim and evidence rather than defending its conclusion. Break the claim
into all material requirements and assess each requirement with a specific passage
or an explicit missing/conflicting relation. Do not invent extra requirements.
Check these distinctions when relevant:
- possibility or mechanism versus observed occurrence;
- association versus causation;
- an example or selected sample versus a general frequency or probability;
- announcement, intention or eligibility versus implementation or guaranteed outcome;
- a population, date, comparison or condition versus a different one;
- absence of support versus actual counterevidence.
Preserve ordinary-language scope. Context is not automatically a universal qualifier.
A narrow statement must not be expanded into an absolute claim. Do not always
abstain: retain supported conclusions when the evidence covers the material claim.
Return a final answer in the required JSON, including the requirements array.
'''


def semantic_messages(case, baseline):
    payload = public_input(case)
    payload['previous_draft'] = {k: baseline[k] for k in ('claim_text', 'verdict', 'citations', 'uncertainty_reason', 'explanation') if isinstance(baseline, dict) and k in baseline}
    return [{'role': 'system', 'content': COMMON + MAP + SEMANTIC_CHECK},
            {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}]


def semantic_config(variant, case):
    result = deepcopy(variant)
    schema = quote_output_schema(case)
    citation_schema = deepcopy(schema['properties']['citations'])
    schema['properties']['requirements'] = {'type': 'array', 'minItems': 1, 'maxItems': 12,
        'items': {'type': 'object', 'additionalProperties': False,
                 'required': ['id', 'text', 'relation', 'citations'],
                 'properties': {'id': {'type': 'string', 'minLength': 1},
                                'text': {'type': 'string', 'minLength': 1},
                                'relation': {'type': 'string', 'enum': ['supports', 'contradicts', 'missing', 'conflicting']},
                                'citations': citation_schema}}}
    schema['required'].append('requirements')
    parameters = dict(result.get('parameters', {}))
    if 'response_format' in parameters:
        raise ValueError('Semantic mode owns response_format')
    parameters['response_format'] = {'type': 'json_schema', 'json_schema': {'name': 'SemanticVerification', 'schema': schema}}
    result['parameters'] = parameters
    return result
