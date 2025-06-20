// Trigger syncQueue when online
window.addEventListener("load", () => {
  if (navigator.onLine) syncQueue();
  window.addEventListener("online", syncQueue);
});

function queueSubmission(formData) {
  const queue = JSON.parse(localStorage.getItem("reportQueue")||"[]");
  queue.push(formData);
  localStorage.setItem("reportQueue", JSON.stringify(queue));
  showOfflinePopup();
}

function syncQueue() {
  const queue = JSON.parse(localStorage.getItem("reportQueue")||"[]");
  console.log("🔄 syncQueue", queue);
  if (!queue.length) return;

  let remaining = [], processed=0, success=0;
  queue.forEach(entry=>{
    console.log("📤 retry entry", entry);
    fetch("/submit-offline", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify(entry)
    })
    .then(res=> {
      console.log("↩️ status", res.status);
      if(res.ok) success++;
      else remaining.push(entry);
    })
    .catch(err=> {
      console.warn("❌ sync error", err);
      remaining.push(entry);
    })
    .finally(()=>{
      processed++;
      if(processed===queue.length){
        localStorage.setItem("reportQueue", JSON.stringify(remaining));
        if(success){
          showOfflinePopup(`✅ ${success} report(s) synced`);
        }
      }
    });
  });
}

function showOfflinePopup(msg) {
  const popup = document.getElementById("offline-popup");
  if(!popup) return alert(msg||"💾 Saved offline.");
  popup.querySelector("p").textContent = msg||"💾 Saved offline. Will auto-submit when back online.";
  popup.classList.remove("hidden");
}
