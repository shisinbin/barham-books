(function () {
  const backdrop = document.getElementById('uiBackdrop');
  let activePanel = null;

  function openPanel(config) {
    if (activePanel) {
      closePanel();
    }

    const { element, inert = [], onOpen } = config;

    element.classList.add('open');
    backdrop.hidden = false;
    backdrop.classList.add('is-visible');
    document.body.style.overflow = 'hidden';

    // inert specified elements
    inert.forEach((el) => el?.setAttribute('inert', ''));

    if (onOpen) onOpen();

    activePanel = config;
  }

  function closePanel() {
    if (!activePanel) return;

    const { element, inert = [], onClose } = activePanel;

    element.classList.remove('open');
    backdrop.classList.remove('is-visible');
    backdrop.hidden = true;
    document.body.style.overflow = '';

    // reactivate
    inert.forEach((el) => el?.removeAttribute('inert'));

    if (onClose) onClose();

    activePanel = null;
  }

  backdrop.addEventListener('click', closePanel);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closePanel();
    }
  });

  window.PanelManager = {
    open: openPanel,
    close: closePanel,
    getActive: () => activePanel,
  };
})();
