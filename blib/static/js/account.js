document.addEventListener('click', async (e) => {
  const btn = e.target.closest('.book-grid__remove');
  if (!btn) return;

  const bookId = btn.dataset.bookId;
  const url = btn.dataset.url;
  const card = btn.closest('[data-book]');

  const formData = new FormData();
  formData.append('book_id', bookId);

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken },
      body: formData,
    });

    const data = await res.json();
    if (data.status === 'ok') {
      card.remove();
      createToast('Interest removed.');
    }
  } catch (err) {
    createToast('Something went wrong.', 'error');
  }
});
