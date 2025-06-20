// combined.js: manage wizard steps and final JSON payload

let currentStep = 1;
const totalSteps = document.querySelectorAll('.wizard-step').length;
const form = document.getElementById('wizard-form');

function showStep(step) {
  document.querySelectorAll('.wizard-step').forEach(section => {
    section.classList.toggle('hidden', Number(section.dataset.step) !== step);
  });
}

// initial display
showStep(currentStep);

// handle Next / Back clicks
document.addEventListener('click', e => {
  if (e.target.matches('.next-button')) {
    if (currentStep < totalSteps) {
      currentStep++;
      showStep(currentStep);
    }
  }
  if (e.target.matches('.back-button')) {
    if (currentStep > 1) {
      currentStep--;
      showStep(currentStep);
    }
  }
});

// on submit, gather all named inputs into one object
form.addEventListener('submit', e => {
  const data = {};
  form.querySelectorAll('input, select, textarea').forEach(el => {
    if (el.name && el.type !== 'submit' && el.name !== 'full_report_json') {
      data[el.name] = el.value;
    }
  });
  document.getElementById('full_report_json').value = JSON.stringify(data);
});
