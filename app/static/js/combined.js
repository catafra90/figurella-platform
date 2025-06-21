// combined.js: dynamic Add buttons + final JSON payload

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('daily-report-form');
  if (!form) return;

  // 1) Handle “+ Add” buttons
  document.querySelectorAll('[data-add-button]').forEach(btn => {
    btn.addEventListener('click', () => {
      const category = btn.getAttribute('data-add-button');
      const container = document.querySelector(`[data-items-container="${category}"]`);
      if (!container) return;

      const template = container.firstElementChild;
      if (!template) return;

      const clone = template.cloneNode(true);
      // Clear inputs and textareas
      clone.querySelectorAll('input, textarea').forEach(el => { el.value = ''; });
      container.appendChild(clone);
    });
  });

  // 2) On submit, gather everything into an object
  form.addEventListener('submit', e => {
    e.preventDefault(); // Prevent normal submission until serialized

    const data = {
      sales: [],
      leads: [],
      consultations: [],
      opportunities: [],
      attendance: {}
    };

    // Helper to collect array sections
    function collectArray(category, fields) {
      const items = [];
      const container = form.querySelector(`[data-items-container="${category}"]`);
      if (!container) return items;

      // Use direct children only
      Array.from(container.children).forEach(block => {
        const obj = {};
        fields.forEach(f => {
          const el = block.querySelector(`[name="${f}[]"]`);
          obj[f] = el ? el.value.trim() : '';
        });
        // only add if at least one field is non-empty
        if (Object.values(obj).some(v => v !== '')) items.push(obj);
      });

      data[category] = items;
    }

    // Collect each category
    collectArray('sales', ['client_name', 'package', 'revenue']);
    collectArray('leads', ['lead_name', 'lead_date', 'lead_source']);
    collectArray('consultations', ['consultation_name', 'consultation_outcome', 'consultation_source']);
    collectArray('opportunities', ['opportunity_name', 'opportunity_provider', 'opportunity_description']);

    // Attendance is a single block
    const attendedEl = form.querySelector('[name="attendance_done"]');
    const noShowEl   = form.querySelector('[name="attendance_noshow"]');
    data.attendance.attendance_done = attendedEl ? attendedEl.value.trim() : '';
    data.attendance.no_show         = noShowEl   ? noShowEl.value.trim()   : '';

    // Create hidden input for JSON payload
    const hidden = document.createElement('input');
    hidden.type = 'hidden';
    hidden.name = 'full_report_json';
    hidden.value = JSON.stringify(data);
    form.appendChild(hidden);

    // Submit the form
    form.submit();
  });
});
