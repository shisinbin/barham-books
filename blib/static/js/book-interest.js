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

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();

    if (data.status !== 'ok') {
      createToast('Something went wrong. Please try again', 'error');
      return;
    }

    if (!data.created) {
      return;
    }

    btn.setAttribute('aria-pressed', 'true');
    btn.disabled = true;

    const isMailSent = data?.mail_sent === true;

    if (isMailSent) {
      createToast(
        "Interest registered - we'll be in touch soon!",
        'success',
      );
    } else {
      createToast(
        "Interest registered, but we couldn't notify staff automatically. Please contact the library if you don't hear back soon.",
        'warning',
      );
    }
  } catch (err) {
    createToast('Something went wrong. Please try again', 'error');
  } finally {
    btn.classList.remove('is-loading');
  }
});
