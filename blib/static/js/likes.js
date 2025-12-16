document.addEventListener('click', async (e) => {
  const link = e.target.closest('a.like');
  if (!link) return;

  e.preventDefault();

  const bookId = link.dataset.id;
  const action = link.dataset.action;
  const url = link.dataset.url;

  const formData = new FormData();
  formData.append('id', bookId);
  formData.append('action', action);

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrftoken },
    body: formData,
  });

  const data = await response.json();

  if (data.status === 'ok') {
    const totalEl = document.querySelector('.count .total');
    const total = parseInt(totalEl.textContent, 10);
    link.dataset.action = action === 'like' ? 'unlike' : 'like';
    link.textContent = action === 'like' ? 'Unlike' : 'Like';
    totalEl.textContent = action === 'like' ? total + 1 : total - 1;
  }
});
