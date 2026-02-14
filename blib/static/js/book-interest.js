document.addEventListener('click', async (e) => {
  const btn = e.target.closest('.js-register-interest');
  if (!btn || btn.disabled || btn.classList.contains('is-loading')) {
    return;
  }

  const root = btn.closest('[data-interest]');
  const bookId = root.dataset.bookId;
  const url = root.dataset.url;

  btn.classList.add('is-loading');

  const formData = new FormData();
  formData.append('book_id', bookId);

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken },
      body: formData,
    });

    const data = await res.json();
    if (data.status !== 'ok' || !data.created) return;

    btn.classList.remove('is-loading');
    btn.setAttribute('aria-pressed', 'true');
    btn.disabled = true;
    createToast(
      "Interest registered - we'll be in touch soon!",
      'success',
    );
  } catch (err) {
    btn.classList.remove('is-loading');
    createToast('Something went wrong. Please try again', 'error');
  }
});
