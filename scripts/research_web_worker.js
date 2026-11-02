// Run in Codex functions.exec with its tools object; this is not a Node web API.
// The worker executes exact model requests, never chooses or rewrites evidence.
async function researchWebWorker(tools, report, cwd, out) {
  const quote = s => "'" + s.replace(/'/g, "'\\''") + "'";
  const read = await tools.exec_command({
    cmd: "cat " + quote(out + "/pending.json"), workdir: cwd, max_output_tokens: 12000
  });
  if (read.exit_code !== 0) throw new Error("Could not read pending requests");
  const pending = JSON.parse(read.output);
  for (const p of pending) {
    if (!/^t\d{3}-s\d{2}$/.test(p.request_id)) throw new Error("Invalid request ID");
    if (!['search', 'read'].includes(p.action)) throw new Error("Invalid action");
  }
  const results = await Promise.allSettled(pending.map(async p => {
    const started = Date.now();
    let raw;
    try {
      raw = await tools.web__run(p.action === "search"
        ? {search_query: [{q: p.query}], response_length: "long"}
        : {open: [{ref_id: p.url}], response_length: "long"});
    } catch (error) {
      raw = "Web worker transport error";
    }
    return {p, response: {request_id: p.request_id, raw, latency_s: (Date.now() - started) / 1000}};
  }));
  for (let i = 0; i < results.length; i++) {
    const item = results[i];
    if (item.status !== "fulfilled") {
      throw new Error("Web worker failed before capturing a response");
    }
    const {p, response} = item.value;
    const relative = out + "/bridge-" + p.request_id + ".json";
    const path = relative.startsWith('/') ? relative : cwd + "/" + relative;
    const patch = "*** Begin Patch\n*** Add File: " + path + "\n" +
      JSON.stringify(response, null, 2).split("\n").map(line => "+" + line).join("\n") + "\n*** End Patch";
    await tools.apply_patch(patch);
    const result = await tools.exec_command({cmd: "python3 scripts/run_research.py ingest --out " +
      quote(out) + " --response " + quote(relative), workdir: cwd, max_output_tokens: 400});
    report({request_id: p.request_id, action: p.action, ingest: result.output});
    if (result.exit_code !== 0) throw new Error("Tool response ingestion failed");
  }
}
