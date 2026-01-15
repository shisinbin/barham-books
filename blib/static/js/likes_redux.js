document.addEventListener('click', async (e) => {
  const btn = e.target.closest('[data-like] .book-like__btn');
  if (!btn || btn.disabled) return;

  const root = btn.closest('[data-like]');

  if (root.dataset.auth !== 'true') {
    createToast('Log in to like books', 'info');
    return;
  }

  const bookId = root.dataset.id;
  const liked = root.dataset.liked == 'true';
  const url = root.dataset.url;

  const formData = new FormData();
  formData.append('id', bookId);
  formData.append('action', liked ? 'unlike' : 'like');

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken },
      body: formData,
    });

    const data = await res.json();
    if (data.status !== 'ok') return;

    root.dataset.liked = (!liked).toString();
    btn.setAttribute('aria-pressed', (!liked).toString());

    const countEl = root.querySelector('.book-like__count');
    countEl.textContent = data.likes > 0 ? data.likes : '';
  } catch (err) {
    createToast('Something went wrong. Please try again.', 'error');
  }
});
