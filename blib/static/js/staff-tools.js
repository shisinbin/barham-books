function initStaffControls() {
  const triggerBtn = document.getElementById('staffTrigger');
  const closeBtn = document.getElementById('staffClose');
  const drawer = document.getElementById('staffDrawer');
  const app = document.querySelector('#app');
  const modalNav = document.querySelector('#modalNav');

  if (!triggerBtn || !closeBtn || !drawer) {
    return;
  }

  const staffConfig = {
    element: drawer,
    inert: [app, modalNav],
    onOpen: () => {
      drawer.classList.add('animating');
      setTimeout(() => {
        drawer.classList.remove('animating');
      }, 300);

      closeBtn.focus();
    },
    onClose: () => {
      drawer.classList.add('animating');
      setTimeout(() => {
        drawer.classList.remove('animating');
      }, 300);

      triggerBtn.focus();
    },
  };

  function openDrawer() {
    window.PanelManager.open(staffConfig);
  }

  function closeDrawer() {
    window.PanelManager.close();
  }

  triggerBtn.addEventListener('click', openDrawer);
  closeBtn.addEventListener('click', closeDrawer);
}

initStaffControls();
