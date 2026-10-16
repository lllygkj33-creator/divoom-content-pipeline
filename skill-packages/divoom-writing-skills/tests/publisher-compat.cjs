// Execute the existing publisher's actual TS parser without starting UI/backend.
// Config/i18n are read-only harness adapters; parsing and validation code are unmodified.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function arg(name) {
  const n=process.argv.indexOf(name);
  if(n<0 || !process.argv[n+1]) throw new Error(`Missing ${name}`);
  return process.argv[n+1];
}
const root=path.resolve(arg('--publisher'));
const jsonPath=path.resolve(arg('--json'));
const ts=require(path.join(root,'node_modules/typescript/lib/typescript.js'));
const config=JSON.parse(fs.readFileSync(path.join(root,'site.config.json'),'utf8').replace(/^\uFEFF/,''));
const sourcePath=path.join(root,'src/lib/shopify-json.ts');
const source=fs.readFileSync(sourcePath,'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const moduleObject={exports:{}};
const site={...config,firstPartySuffixes:config.firstPartySuffixes,storefrontDomain:config.storefront.domain};
const channels=config.channels.map(c=>({...c,pageSpec:c.page}));
const allowed={
  '@/config/site':{ALL_CHANNELS:channels,site},
  '@/i18n':{getLang:()=> 'en',t:(key,params)=>key+(params?JSON.stringify(params):'')},
  '@/i18n/channel-label':{channelLabel:c=>c.name}
};
const context={module:moduleObject,exports:moduleObject.exports,URL,console,require:(name)=>{
  if(!(name in allowed)) throw new Error('Unexpected import: '+name);
  return allowed[name];
}};
vm.runInNewContext(compiled,context,{filename:sourcePath});
const result=moduleObject.exports.parseJsonContent(fs.readFileSync(jsonPath,'utf8'),jsonPath,'custom');
const rows=result.candidates.map(c=>({title:c.title,blog:c.blogName,tags:c.tags,publishable:c.publishable,issues:c.issues}));
const errors=rows.flatMap(r=>r.issues.filter(i=>i.level==='error'));
console.log(JSON.stringify({parser:sourcePath,parserSha256:require('node:crypto').createHash('sha256').update(source).digest('hex'),mode:'actual parser; config and translation adapters; custom upload target; no service and no publishing',detected:result.detected,error:result.error,candidates:rows},null,2));
if(result.error || !rows.length || errors.length) process.exitCode=1;
