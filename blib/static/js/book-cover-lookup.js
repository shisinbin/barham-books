(function () {
  const app = document.getElementById('cover-lookup-app');
  if (!app) return;

  const candidatesUrl = app.dataset.candidatesUrl;
  const attachUrl = app.dataset.attachUrl;
  const bookDetailUrl = app.dataset.bookDetailUrl;

  const findBtn = document.getElementById('find-covers-btn');
  const attachBtn = document.getElementById('attach-btn');
  const grid = document.getElementById('cover-grid');
  const loadingIndicator = document.getElementById(
    'loading-indicator'
  );

  let selectedCoverUrl = null;

  // ------------- helpers ----------------

  function showError(msg) {
    if (window.createToast) {
      createToast(msg, 'error');
    } else {
      alert(msg);
    }
  }

  function showSuccess(msg) {
    if (window.createToast) {
      createToast(msg, 'success');
    } else {
      alert(msg);
    }
  }

  function clearSelection() {
    selectedCoverUrl = null;
    attachBtn.disabled = true;

    grid
      .querySelectorAll('.cover-option.selected')
      .forEach((el) => el.classList.remove('selected'));
  }

  // ------------- render ----------------

  function renderCandidates(candidates) {
    grid.innerHTML = '';
    clearSelection();

    if (!candidates.length) {
      showError('No cover images found for this book.');
      return;
    }

    // const p = document.createElement('p');
    // p.style.marginBlock = '24px';
    // p.textContent = 'Select one of the following images:';
    // grid.insertAdjacentElement('beforebegin', p);

    for (const c of candidates) {
      const div = document.createElement('div');
      div.className = 'cover-option';
      div.dataset.url = c.url;

      const img = document.createElement('img');
      img.src = c.url;
      img.loading = 'lazy';

      img.onerror = function () {
        div.remove();
      };

      img.onload = function () {
        if (this.naturalWidth <= 5 || this.naturalHeight <= 5) {
          div.remove();
        }
      };

      const meta = document.createElement('div');
      meta.className = 'meta';
      meta.textContent = `${c.source} · rank ${c.result_rank ?? '?'}`;

      div.appendChild(img);
      div.appendChild(meta);

      // div.innerHTML = `
      //   <img src="${c.url}" loading="lazy">
      //   <div class="meta" aria-hidden="true">
      //     ${c.source} · rank ${c.result_rank ?? '?'}
      //   </div>
      // `;

      div.addEventListener('click', () => {
        selectCover(div);
      });

      grid.appendChild(div);
    }
  }

  function selectCover(div) {
    grid
      .querySelectorAll('.cover-option.selected')
      .forEach((el) => el.classList.remove('selected'));

    div.classList.add('selected');
    selectedCoverUrl = div.dataset.url;
    attachBtn.disabled = false;
  }

  // ------------- actions ----------------

  findBtn.addEventListener('click', () => {
    findBtn.disabled = true;
    loadingIndicator.style.display = 'inline';

    fetch(candidatesUrl, {
      headers: {
        'X-CSRFToken': csrftoken,
      },
    })
      .then((r) => r.json())
      .then((data) => {
        if (!data.ok) {
          throw new Error(
            data.error || 'Failed to fetch cover candidates.'
          );
        }

        renderCandidates(data.candidates);
      })
      .catch((err) => {
        console.error(err);
        showError(err.message || 'Error looking up cover images.');
      })
      .finally(() => {
        findBtn.disabled = false;
        loadingIndicator.style.display = 'none';
      });
  });

  attachBtn.addEventListener('click', () => {
    if (!selectedCoverUrl) return;

    attachBtn.disabled = true;

    fetch(attachUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
      },
      body: JSON.stringify({
        cover_url: selectedCoverUrl,
      }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (!data.ok) {
          throw new Error(
            data.error || 'Failed to attach cover image.'
          );
        }

        window.location.href = bookDetailUrl;
        showSuccess('Cover image attached successfully.');
      })
      .catch((err) => {
        console.error(err);
        showError(err.message || 'Error attaching cover image.');
        attachBtn.disabled = false;
      });
  });
})();
