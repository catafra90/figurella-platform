const CACHE = "figurella-v1";
const OFFLINE = "/offline";

const toCache = [
  "/", "/step1/", "/step2/", "/step3/", "/step4/", "/step5/", "/clients", "/offline",
  "/static/css/tailwind.min.css",
  "/static/js/sw-init.js", "/static/js/queue.js",
  "/static/images/figurella-logo.png",
  "/static/manifest.json"
];

self.addEventListener("install", e=>{
  e.waitUntil(
    caches.open(CACHE).then(c=>c.addAll(toCache))
  );
  self.skipWaiting();
});

self.addEventListener("activate", e=>{
  e.waitUntil(
    caches.keys().then(keys=>Promise.all(
      keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener("fetch", e=>{
  if(e.request.method!=="GET") return;
  e.respondWith(
    caches.match(e.request,{ignoreSearch:true})
      .then(r=>r||fetch(e.request)
        .then(resp=>{
          if(resp.ok && resp.type==="basic"){
            let clone = resp.clone();
            caches.open(CACHE).then(c=>c.put(e.request, clone));
          }
          return resp;
        })
        .catch(()=>caches.match(OFFLINE))
      )
  );
});
