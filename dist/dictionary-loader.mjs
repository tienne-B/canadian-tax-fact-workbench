// Compose referenced modules; only explicitly declared derived aggregates may be replaced.
export async function loadDictionaries(read, manifestPath='./dictionary-modules.json') {
 const manifest=JSON.parse(await read(manifestPath)),ids=new Set(),facts=new Map(),xmlFacts=new Map();
 for(const module of manifest.modules){
  if(ids.has(module.id))throw Error('Duplicate dictionary module: '+module.id);
  for(const required of module.requires)if(!ids.has(required))throw Error('Missing or unordered module: '+required);
  const [c,x]=await Promise.all([read(module.catalogue),read(module.dictionary)]),cat=JSON.parse(c);
  const body=x.match(/<Facts>([\s\S]*?)<\/Facts>/)?.[1];if(!body)throw Error('Missing Facts: '+module.dictionary);
  const replacements=new Set(module.replaces??[]),incoming=new Map(),incomingXml=new Map();
  for(const f of cat.facts){if(incoming.has(f.path))throw Error('Duplicate catalogue fact: '+f.path);incoming.set(f.path,f);}
  for(const match of body.matchAll(/<Fact\s+path="([^"]+)"[^>]*>[\s\S]*?<\/Fact>/g)){
   if(incomingXml.has(match[1]))throw Error('Duplicate XML fact: '+match[1]);incomingXml.set(match[1],match[0]);
  }
  for(const path of replacements){
   if(!facts.get(path)?.formula||!incoming.get(path)?.formula||!xmlFacts.has(path)||!incomingXml.has(path))throw Error('Replacement must target an existing derived fact: '+path);
  }
  for(const [path,xml]of incomingXml){if(xmlFacts.has(path)&&!replacements.has(path))throw Error('Duplicate XML fact: '+path);xmlFacts.set(path,xml);}
  for(const [path,f]of incoming){if(facts.has(path)&&!replacements.has(path))throw Error('Duplicate catalogue fact: '+path);facts.set(path,{...f,dictionaryModule:module.id});}
  ids.add(module.id);
 }
 for(const path of facts.keys())if(!xmlFacts.has(path))throw Error('Missing XML definition: '+path);
 return {catalogue:{version:manifest.version,modules:manifest.modules,facts:[...facts.values()]},xml:'<FactDictionaryModule><Facts>'+[...xmlFacts.values()].join('\n')+'</Facts></FactDictionaryModule>'};
}
