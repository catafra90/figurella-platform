// combined.js: dynamic Add buttons + JSON POST only when online

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('daily-report-form');
  if (!form) return;

  // Handle “+ Add” buttons
  document.querySelectorAll('[data-add-button]').forEach(btn => {
    btn.addEventListener('click', () => {
      const category = btn.getAttribute('data-add-button');
      const container = document.querySelector(`[data-items-container="${category}"]`);
      const template = container.firstElementChild;
      const clone = template.cloneNode(true);
      clone.querySelectorAll('input, textarea').forEach(el => el.value = '');
      container.appendChild(clone);
    });
  });

  // On submit, gather data into object
  form.addEventListener('submit', e => {
    e.preventDefault();

    const data = { sales: [], leads: [], consultations: [], opportunities: [], attendance: {} };

    function collect(category, fields) {
      const items = [];
      const container = form.querySelector(`[data-items-container="${category}"]`);
      Array.from(container.children).forEach(block => {
        const obj = {};
        fields.forEach(f => {
          const el = block.querySelector(`[name="${f}[]"]`);
          obj[f] = el ? el.value.trim() : '';
        });
        if (Object.values(obj).some(v => v !== '')) items.push(obj);
      });
      data[category] = items;
    }

    collect('sales', ['client_name', 'package', 'revenue']);
    collect('leads', ['lead_name', 'lead_date', 'lead_source']);
    collect('consultations', ['consultation_name', 'consultation_outcome', 'consultation_source']);
    collect('opportunities', ['opportunity_name', 'opportunity_provider', 'opportunity_description']);
    data.attendance.attendance_done = form.querySelector('[name="attendance_done"]').value.trim();
    data.attendance.no_show         = form.querySelector('[name="attendance_noshow"]').value.trim();

    // Submit online only
    const hidden = document.createElement('input');
    hidden.type = 'hidden';
    hidden.name = 'full_report_json';
    hidden.value = JSON.stringify(data);
    form.appendChild(hidden);
    form.submit();
  });
});
