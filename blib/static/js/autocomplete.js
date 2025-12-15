/*
  This file will:
  - attach to #keywords input field
  - fetch /books/autocomplete?term=...
  - render a dropdown
  - handle click + keyboard

  Reference:
  https://dev.to/alexpechkarev/how-to-build-an-autocomplete-component-from-scratch-in-vanilla-js-45g0
  https://codepen.io/alexpechkarev/pen/PwPydQB?editors=1010
*/

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('keywords');
  if (!input) return;

  let selectedIndex = -1;
  let suggestions = [];
  let dropdown = null;

  function clearDropdown() {
    if (dropdown) {
      dropdown.remove();
      dropdown = null;
    }
    suggestions = [];
    selectedIndex = -1;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
  }

  function updateSelected() {
    suggestions.forEach((li, index) => {
      const active = index === selectedIndex;

      li.classList.toggle('active', active);

      if (active) {
        li.scrollIntoView({ block: 'nearest' });
        input.setAttribute('aria-activedescendant', li.id);
      }
    });
  }

  function positionDropdown() {
    if (!dropdown) return;

    const rect = input.getBoundingClientRect();
    dropdown.style.width = `${rect.width}px`;
    dropdown.style.left = `${rect.left + window.scrollX}px`;
    dropdown.style.top = `${rect.bottom + window.scrollY}px`;
  }

  function renderDropdown(results) {
    clearDropdown();

    dropdown = document.createElement('ul');
    dropdown.id = 'autocomplete-list';
    dropdown.className = 'autocomplete-list';
    dropdown.setAttribute('role', 'listbox');

    input.setAttribute('aria-expanded', 'true');

    results.forEach((item, index) => {
      const li = document.createElement('li');
      li.id = `suggestion-${index}`;
      li.setAttribute('role', 'option');
      li.textContent = item.label;

      li.addEventListener('mousedown', () => {
        window.location.href = item.url;
      });

      dropdown.appendChild(li);
      suggestions.push(li);
    });

    document.body.appendChild(dropdown);
    positionDropdown();
  }

  /*
    INPUT EVENT LISTENER
  */
  input.addEventListener('input', async () => {
    const term = input.value.trim();

    if (term.length < 3) {
      clearDropdown();
      return;
    }

    const response = await fetch(
      `autocomplete/?term=${encodeURIComponent(term)}`
    );
    const results = await response.json();

    if (results.length === 0) {
      clearDropdown();
      return;
    }

    renderDropdown(results);
  });

  input.addEventListener('blur', () => {
    setTimeout(clearDropdown, 150);
  });

  /*
    KEYDOWN EVENT LISTENER
  */
  input.addEventListener('keydown', (e) => {
    if (!dropdown || !suggestions.length) return;

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

    if (e.key === 'Escape') {
      clearDropdown();
    }
  });

  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown?.contains(e.target)) {
      clearDropdown();
    }
  });

  window.addEventListener('resize', positionDropdown);
  window.addEventListener('scroll', positionDropdown);
});
