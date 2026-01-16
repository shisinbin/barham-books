function initStaffControls() {
  const triggerBtn = document.getElementById('staffTrigger');
  const closeBtn = document.getElementById('staffClose');
  const drawer = document.getElementById('staffDrawer');

  if (!triggerBtn || !closeBtn || !drawer) {
    return;
  }

  function openDrawer() {
    drawer.classList.add('open');
    closeBtn.focus();
    document.body.style.overflow = 'hidden';
  }

  function closeDrawer() {
    drawer.classList.remove('open');
    triggerBtn.focus();
    document.body.style.overflow = '';
  }

  triggerBtn.addEventListener('click', openDrawer);
  closeBtn.addEventListener('click', closeDrawer);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && drawer.classList.contains('open')) {
      closeDrawer();
    }
  });

  window.addEventListener('click', (e) => {
    if (
      drawer.classList.contains('open') &&
      !drawer.contains(e.target) &&
      !triggerBtn.contains(e.target)
    ) {
      closeDrawer();
    }
  });
}

initStaffControls();
