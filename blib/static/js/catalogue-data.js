function init() {
  const form = document.querySelector('.catalogue-data__form');
  if (!form) return;

  form.addEventListener('submit', () => {
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Preparing download...';
  });
}

init();
