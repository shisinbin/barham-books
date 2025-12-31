document.addEventListener('DOMContentLoaded', () => {
  document
    .querySelectorAll('[data-autocomplete]')
    .forEach(initAutocomplete);
});

function initAutocomplete(container) {
  const input = container.querySelector('input');
  const listbox = container.querySelector('.search__autocomplete');
  const endpoint = container.dataset.autocompleteUrl;
  let controller;

  let suggestions = [];
  let selectedIndex = -1;

  function clear() {
    listbox.hidden = true;
    listbox.innerHTML = '';
    suggestions = [];
    selectedIndex = -1;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
  }

  function render(results) {
    clear();

    results.forEach((item, i) => {
      const li = document.createElement('li');
      li.id = `search-option-${i}`;
      li.role = 'option';
      li.textContent = item.label;

      li.addEventListener('mousedown', () => {
        window.location.href = item.url;
      });

      listbox.appendChild(li);
      suggestions.push(li);
    });

    listbox.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }

  function updateSelected() {
    suggestions.forEach((li, i) => {
      const active = i === selectedIndex;

      li.classList.toggle('active', active);

      if (active) {
        input.setAttribute('aria-activedescendant', li.id);
      }
    });
  }

  input.addEventListener('input', async () => {
    const term = input.value.trim();
    if (term.length < 3) return clear();

    controller?.abort();
    controller = new AbortController();

    const res = await fetch(
      `${endpoint}?term=${encodeURIComponent(term)}`,
      { signal: controller.signal }
    );
    const data = await res.json();

    if (data.length === 0) return clear();

    render(data);
  });

  input.addEventListener('keydown', (e) => {
    if (suggestions.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = (selectedIndex + 1) % suggestions.length;
      updateSelected();
    }

    if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex =
        (selectedIndex - 1 + suggestions.length) % suggestions.length;
      updateSelected();
    }

    if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      suggestions[selectedIndex].dispatchEvent(
        new MouseEvent('mousedown')
      );
    }

    if (e.key === 'Escape') clear();
  });

  document.addEventListener(
    'click',
    (e) => {
      if (!container.contains(e.target)) clear();
    },
    true
  );
}
