const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../scripts/recovery_web_worker.js'),'utf8');
const sandbox={};vm.createContext(sandbox);vm.runInContext(source,sandbox);
(async()=>{
  const pending=[0,1,2].map(i=>({request_id:`t00${i}-s01`,action:'search',query:'query '+i}));
  const saved=[];let webCalls=0;let ingestCalls=0;let fail=true;let cached=[];
  const tools={
    async exec_command(args){
      if(args.cmd.startsWith('python3 -c '))return {exit_code:0,output:JSON.stringify({pending,cached})};
      assert.equal(saved.length,3,'all web responses must be durable before any ingestion');
      ingestCalls++;
      return {exit_code:fail?2:0,output:fail?'runner lock busy':'ingested'};
    },
    async web__run(){webCalls++;return 'raw tool result';},
    async apply_patch(patch){saved.push(patch);return {};}
  };
  await sandbox.recoveryWebWorker(tools,()=>{},'/repo','results/run');
  assert.equal(webCalls,3);assert.equal(saved.length,3);assert.equal(ingestCalls,1);
  cached=pending.map(p=>'bridge-'+p.request_id+'.json');fail=false;
  await sandbox.recoveryWebWorker(tools,()=>{},'/repo','results/run');
  assert.equal(webCalls,3,'cached response handoff must not repeat network requests');
  assert.equal(ingestCalls,4);
  console.log('PASS: persist all before ingest; reuse cached responses after a lock failure');
})().catch(error=>{console.error(error);process.exitCode=1;});
