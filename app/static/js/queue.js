// app/static/js/queue.js

// On page load, if we’re online, try to sync any queued reports.
// Also listen for the browser coming back online.
window.addEventListener("load", () => {
  if (navigator.onLine) syncQueue();
  window.addEventListener("online", syncQueue);
});

/**
 * Call this instead of fetch() when offline.
 * It saves the report payload to localStorage and shows a popup.
 */
function queueSubmission(formData) {
  const queue = JSON.parse(localStorage.getItem("reportQueue") || "[]");
  queue.push(formData);
  localStorage.setItem("reportQueue", JSON.stringify(queue));
  showOfflinePopup("💾 Saved offline. Will auto-submit when back online.");
}

/**
 * Attempts to resend any queued submissions.
 * On success, pops a success message.
 */
function syncQueue() {
  const queue = JSON.parse(localStorage.getItem("reportQueue") || "[]");
  if (!queue.length) return;

  let remaining = [], processed = 0, successCount = 0;

  queue.forEach(entry => {
    fetch("/daily-report/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry)
    })
    .then(res => {
      if (res.ok) successCount++;
      else remaining.push(entry);
    })
    .catch(() => {
      remaining.push(entry);
    })
    .finally(() => {
      processed++;
      if (processed === queue.length) {
        localStorage.setItem("reportQueue", JSON.stringify(remaining));
        if (successCount > 0) {
          showOfflinePopup(`✅ ${successCount} report(s) synced.`);
        }
      }
    });
  });
}

/**
 * Utility to show a simple modal popup for offline/online messages.
 * Expects an element with id="offline-popup" and a <p> inside with id="offline-popup-msg".
 */
function showOfflinePopup(msg) {
  const popup = document.getElementById("offline-popup");
  if (!popup) return alert(msg);
  popup.querySelector("#offline-popup-msg").textContent = msg;
  popup.classList.remove("hidden");
}

