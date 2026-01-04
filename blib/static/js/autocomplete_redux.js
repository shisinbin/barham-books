// const STOPWORDS = [
//   "the","and","for","with","from","that","this","into","onto","over","under",
//   "about","after","before","between","through","without","within","upon",
//   "book","books","novel","novels","story","stories"
// ];

// This has to align with stopwords used in the view !!!
const STOPWORDS = [
  'the',
  'and',
  'for',
  'with',
  'from',
  'that',
  'this',
  'into',
  'onto',
];

function normaliseQuery(q) {
  if (!q) return '';

  return q
    .toLowerCase()
    .normalize('NFKD') // normalises accents
    .replace(/[^\w\s]/g, ' ') // remove special characters
    .split(/\s+/) // split into words
    .filter(
      (word) =>
        word.length >= 3 && // keeps words >= 3 chars
        !STOPWORDS.includes(word) // filters stopwords
    )
    .join(' ')
    .trim();
}

document.addEventListener('DOMContentLoaded', () => {
  document
    .querySelectorAll('[data-autocomplete]')
    .forEach(initAutocomplete);
});

function initAutocomplete(container) {
  const input = container.querySelector('input');
  const listbox = container.querySelector('.search__autocomplete');
  const endpoint = container.dataset.autocompleteUrl;

  // state to help stop hammering db unnecessarily
  let lastEffectiveQuery = '';
  let lastHadResults = true;

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
    try {
      const raw = input.value.trim();

      if (raw.length < 3) {
        clear();
        lastEffectiveQuery = '';
        lastHadResults = true;
        return;
      }

      const effectiveQuery = normaliseQuery(raw);
      if (!effectiveQuery) return;

      // if last query returned zero results and new query only extends it, exit
      if (
        !lastHadResults &&
        effectiveQuery.startsWith(lastEffectiveQuery)
      ) {
        return;
      }

      // updates state
      lastEffectiveQuery = effectiveQuery;

      controller?.abort();
      controller = new AbortController();

      const res = await fetch(
        `${endpoint}?term=${encodeURIComponent(effectiveQuery)}`,
        { signal: controller.signal }
      );
      const data = await res.json();

      // updates state
      lastHadResults = data.length > 0;

      if (data.length === 0) {
        clear();
        return;
      }

      render(data);
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error(err);
      }
    }
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
