window.addEventListener("load", () => {
  if (navigator.onLine) {
    syncQueue();
  }

  window.addEventListener("online", syncQueue);
});

function queueSubmission(formData) {
  const queue = JSON.parse(localStorage.getItem("reportQueue") || "[]");
  queue.push(formData);
  localStorage.setItem("reportQueue", JSON.stringify(queue));
  alert("💾 Saved offline. Will auto-submit once online.");
}

function syncQueue() {
  const queue = JSON.parse(localStorage.getItem("reportQueue") || "[]");
  if (!queue.length) return;

  const remainingQueue = [];
  let processed = 0;
  let successCount = 0;

  queue.forEach((entry) => {
    fetch("/step5", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry),
    })
      .then((res) => {
        if (res.ok) {
          successCount++;
        } else {
          remainingQueue.push(entry);
        }
      })
      .catch(() => {
        remainingQueue.push(entry);
      })
      .finally(() => {
        processed++;
        if (processed === queue.length) {
          localStorage.setItem("reportQueue", JSON.stringify(remainingQueue));
          if (successCount > 0) {
            alert(`✅ ${successCount} report(s) synced successfully.`);
          }
        }
      });
  });
}
