function initNavModal() {
  const navOpenBtn = document.querySelector('#navOpenBtn');
  const navCloseBtn = document.querySelector('#navCloseBtn');
  const modalNav = document.querySelector('#modalNav');
  const app = document.querySelector('#app');
  const staffDrawer = document.querySelector('#staffDrawer');

  if (!navOpenBtn || !navCloseBtn || !modalNav) {
    return;
  }

  const breakpoint = window.matchMedia('(width < 600px)');

  const navConfig = {
    element: modalNav,
    inert: [app, staffDrawer].filter(Boolean),
    onOpen: () => {
      modalNav.classList.add('animating');
      setTimeout(() => {
        modalNav.classList.remove('animating');
      }, 300);

      modalNav.removeAttribute('inert');
      navOpenBtn.setAttribute('aria-expanded', 'true');
      navCloseBtn.focus();
    },
    onClose: () => {
      modalNav.classList.add('animating');
      setTimeout(() => {
        modalNav.classList.remove('animating');
      }, 300);

      modalNav.setAttribute('inert', '');
      navOpenBtn.setAttribute('aria-expanded', 'false');
      navOpenBtn.focus();
    },
  };

  function openMobileMenu() {
    window.PanelManager.open(navConfig);
  }

  function closeMobileMenu() {
    window.PanelManager.close();
  }

  navOpenBtn.addEventListener('click', openMobileMenu);
  navCloseBtn.addEventListener('click', closeMobileMenu);

  function setupTopNav() {
    if (breakpoint.matches) {
      // console.log('is mobile');
      modalNav.setAttribute('inert', '');
    } else {
      // console.log('is desktop');
      if (window.PanelManager.getActive()?.element === modalNav) {
        window.PanelManager.close();
      }
      modalNav.removeAttribute('inert');
    }
  }

  breakpoint.addEventListener('change', setupTopNav);
  setupTopNav();

  // function animateMenu() {
  //   modalNav.classList.add('animating');

  //   setTimeout(() => {
  //     modalNav.classList.remove('animating');
  //   }, 300);
  // }
}

initNavModal();

/*
  We could use focus-trap instead here to:
  - trap focus in the modal
  - handle click outside
  - handle pressing escape key

  But instead we are doing this stuff ourselves - mostly.
  The one difference is that we aren't completely locking
  focus inside the modal - they can focus outside in the dev
  area for example. Which actually is correct.

  To use focus-trap, we'd import their scripts into index.html:

  <script src="https://unpkg.com/tabbable/dist/index.umd.js"></script>
  <script src="https://unpkg.com/focus-trap/dist/focus-trap.umd.js"></script>

  This gives us access to 'focusTrap'.

  So then, here we'd do something like:

  const trap = focusTrap.createFocusTrap(modalNav, {
    onDeactivate: () => {
      closeMobileMenu();
    },
    clickOutsideDeactivates: true,
    escapeDeactivates: true,
  });

  and inside the open menu function:

  trap.activate()

  and inside the close menu function:

  trap.deactivate()

  and that's it.
*/
