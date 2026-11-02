// Codex functions.exec worker. Persist every raw response before ingesting any.
async function authorityV2WebWorker(tools, report, cwd, out) {
  const quote = s => "'" + s.replace(/'/g, "'\\''") + "'";
  const preflight = "import fcntl,json,pathlib; p=pathlib.Path(" + JSON.stringify(out) + "); f=(p/'runner.lock').open('a'); fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB); s=json.loads((p/'state.json').read_text()); assert s.get('in_flight') is None, 'API call in progress'; print(json.dumps({'pending':json.loads((p/'pending.json').read_text()),'cached':[x.name for x in p.glob('bridge-*.json')]}))";
  const read = await tools.exec_command({cmd:"python3 -c " + quote(preflight),workdir:cwd,max_output_tokens:14000});
  if (read.exit_code !== 0) {report({status:"runner_busy_or_unavailable",detail:read.output}); return;}
  const {pending,cached}=JSON.parse(read.output);
  for (const p of pending) if(!/^t\d{3}-s\d{2}$/.test(p.request_id) || !['search','read'].includes(p.action)) throw Error('Invalid request');
  const jobs=pending.filter(p=>!cached.includes('bridge-'+p.request_id+'.json'));
  const results=await Promise.allSettled(jobs.map(async p=>{
    const start=Date.now();let raw;
    try {raw=await tools.web__run(p.action==='search'?{search_query:[{q:p.query}],response_length:'long'}:{open:[{ref_id:p.url}],response_length:'long'});}
    catch(error) {raw='Web worker transport error';}
    return {p,response:{request_id:p.request_id,raw,latency_s:(Date.now()-start)/1000}};
  }));
  for(const result of results){
    if(result.status!=='fulfilled')throw Error('Response capture failed');
    const {p,response}=result.value;
    const relative=out+'/bridge-'+p.request_id+'.json';
    const path=relative.startsWith('/')?relative:cwd+'/'+relative;
    await tools.apply_patch('*** Begin Patch\n*** Add File: '+path+'\n'+JSON.stringify(response,null,2).split('\n').map(l=>'+'+l).join('\n')+'\n*** End Patch');
  }
  for(const p of pending){
    const response=out+'/bridge-'+p.request_id+'.json';
    const result=await tools.exec_command({cmd:'python3 scripts/run_authority_v2.py ingest --out '+quote(out)+' --response '+quote(response),workdir:cwd,max_output_tokens:400});
    report({request_id:p.request_id,action:p.action,cached:cached.includes('bridge-'+p.request_id+'.json'),ingest:result.output});
    if(result.exit_code!==0)return; // All responses are durable; next run reuses them.
  }
}
