function initStaffControls() {
  const triggerBtn = document.getElementById('staffTrigger');
  const closeBtn = document.getElementById('staffClose');
  const drawer = document.getElementById('staffDrawer');

  if (!triggerBtn || !closeBtn || !drawer) {
    return;
  }

  const staffInvertable = [
    document.querySelector('#app'),
    document.querySelector('#modalNav'),
  ];

  const staffConfig = {
    element: drawer,
    inert: staffInvertable,
    onOpen: () => closeBtn.focus(),
    onClose: () => triggerBtn.focus(),
  };

  function openDrawer() {
    openPanel(staffConfig);
  }

  function closeDrawer() {
    closePanel();
  }

  triggerBtn.addEventListener('click', openDrawer);
  closeBtn.addEventListener('click', closeDrawer);
}

initStaffControls();
