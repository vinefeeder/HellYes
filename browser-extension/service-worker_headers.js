// background.js  – classic “Copy‑as‑cURL (POSIX)” generator
// ---------------------------------------------------------
const tabData = {};

function store(tabId, k, v) {
  if (tabId < 0) return;
  tabData[tabId] ??= {};
  tabData[tabId][k] = v;
}

function bytesToEsc(raw) {
  return [...new Uint8Array(raw)]
         .map(b => "\\x" + b.toString(16).padStart(2, "0")).join("");
}

// --- sniff network ----------------------------------------------------------
chrome.webRequest.onCompleted.addListener(
  d => { if (d.method==="GET" && /manifest|license/i.test(d.url))
           store(d.tabId,"manifestUrl",d.url); },
  {urls:["<all_urls>"]}
);

chrome.webRequest.onBeforeRequest.addListener(
  d => {
    if (d.method!=="POST" || !/license/i.test(d.url)) return;
    const raw = d.requestBody?.raw?.[0]?.bytes;
    if (!raw) return;
    store(d.tabId,"licenseUrl",d.url);
    store(d.tabId,"bodyEsc",   bytesToEsc(raw));
  },
  {urls:["<all_urls>"]}, ["requestBody"]
);

chrome.webRequest.onBeforeSendHeaders.addListener(
  d => {
    if (d.method!=="POST" || !/license/i.test(d.url)) return;
    const hdr = d.requestHeaders
                 .map(h => ` -H '${h.name}: ${h.value}'`).join("");
    store(d.tabId,"headerStr",hdr);
  },
  {urls:["<all_urls>"]}, ["requestHeaders"]
);

// --- helper to build the one‑liner ------------------------------------------
function buildCurl(info){
  if(!info.licenseUrl||!info.headerStr||!info.bodyEsc) return "";
  return `curl '${info.licenseUrl}'${info.headerStr} --data-raw $'${info.bodyEsc}'`;
}

// --- popup -> native host ----------------------------------------------------
chrome.runtime.onMessage.addListener((msg,sender,reply)=>{
  if(msg.action!=="sendData") return;
  chrome.tabs.query({active:true,currentWindow:true},tabs=>{
    const id=tabs[0]?.id, info=tabData[id];
    if(!info) return reply({status:"error",error:"no data"});
    chrome.runtime.sendNativeMessage(
      "org.hellyes.hellyes",
      {
        manifestUrl: info.manifestUrl||"",
        licenseCurl: buildCurl(info),
        title      : info.title||"video",
        deleteMe   : true
      },
      r=>reply(r??{status:"error",error:"native host failed"})
    );
  });
  return true;
});
