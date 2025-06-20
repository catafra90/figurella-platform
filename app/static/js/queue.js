// static/js/queue.js

// Trigger syncQueue when online
window.addEventListener("load", () => {
  if (navigator.onLine) syncQueue();
  window.addEventListener("online", syncQueue);
});

// Save report if offline
function queueSubmission(formData) {
  const queue = JSON.parse(localStorage.getItem("reportQueue") || "[]");
  queue.push(formData);
  localStorage.setItem("reportQueue", JSON.stringify(queue));
  showPopup("💾 Saved offline. Will auto-submit once online.");
}

// Sync offline queue when back online
function syncQueue() {
  const queue = JSON.parse(localStorage.getItem("reportQueue") || "[]");
  if (!queue.length) return;

  const remaining = [];
  let processed = 0, synced = 0;

  queue.forEach(entry => {
    fetch("/submit-offline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry),
    }).then(res => {
      if (res.ok) synced++;
      else remaining.push(entry);
    }).catch(() => remaining.push(entry))
      .finally(() => {
        processed++;
        if (processed === queue.length) {
          localStorage.setItem("reportQueue", JSON.stringify(remaining));
          if (synced > 0) {
            showPopup(`✅ ${synced} offline report(s) submitted successfully.`);
          }
        }
      });
  });
}

// Helper to display message popup
function showPopup(message) {
  const popup = document.getElementById("popup");
  if (!popup) return alert(message);
  popup.querySelector("p").textContent = message;
  popup.classList.remove("hidden");
}
