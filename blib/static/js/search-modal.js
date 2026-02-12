function initSearchModal() {
  const searchOpenBtn = document.getElementById('searchOpenBtn');
  const searchCloseBtn = document.getElementById('searchCloseBtn');
  const searchModalInput = document.getElementById(
    'searchModalInput',
  );
  const modalSearch = document.getElementById('modalSearch');
  const app = document.getElementById('app');
  const modalNav = document.getElementById('modalNav');
  const staffDrawer = document.getElementById('staffDrawer');

  if (!searchOpenBtn || !modalSearch || !searchModalInput) {
    return;
  }

  const searchConfig = {
    element: modalSearch,
    inert: [app, modalNav, staffDrawer].filter(Boolean),
    onOpen: () => {
      modalSearch.classList.add('animating');
      setTimeout(() => {
        modalSearch.classList.remove('animating');
      }, 300);

      modalSearch.removeAttribute('inert');
      searchOpenBtn.setAttribute('aria-expanded', 'true');
      searchModalInput.focus();
      searchModalInput.select();
    },
    onClose: () => {
      modalSearch.classList.add('animating');
      setTimeout(() => {
        modalSearch.classList.remove('animating');
      }, 300);

      modalSearch.setAttribute('inert', '');
      searchOpenBtn.setAttribute('aria-expanded', 'false');
      searchOpenBtn.focus();
    },
  };

  searchOpenBtn.addEventListener('click', () =>
    window.PanelManager.open(searchConfig),
  );
  searchCloseBtn?.addEventListener('click', () =>
    window.PanelManager.close(),
  );
}

initSearchModal();
