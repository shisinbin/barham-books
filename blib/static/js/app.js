// document.getElementById('current-year').textContent =
//   new Date().getFullYear();

/* ~~~~~~~~~~~ BACKDROP ~~~~~~~~~~~~~ */
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

/* ~~~~~~~~~~~~~~~ END BACKDROP ~~~~~~~~~~~~~~~~ */

const btnOpen = document.querySelector('#btnOpen');
const btnClose = document.querySelector('#btnClose');
const modalNav = document.querySelector('#modalNav');
const breakpoint = window.matchMedia('(width < 600px)');

const navInertable = [
  document.querySelector('#app'),
  document.querySelector('#staffDrawer'),
];

const navConfig = {
  element: modalNav,
  inert: navInertable,
  onOpen: () => {
    modalNav.classList.add('animating');
    setTimeout(() => {
      modalNav.classList.remove('animating');
    }, 300);

    modalNav.removeAttribute('inert');
    btnOpen.setAttribute('aria-expanded', 'true');
    btnClose.focus();
  },
  onClose: () => {
    modalNav.classList.add('animating');
    setTimeout(() => {
      modalNav.classList.remove('animating');
    }, 300);

    modalNav.setAttribute('inert', '');
    btnOpen.setAttribute('aria-expanded', 'false');
    btnOpen.focus();
  },
};

// let isMenuOpen = false;

btnOpen.addEventListener('click', openMobileMenu);
btnClose.addEventListener('click', closeMobileMenu);
breakpoint.addEventListener('change', setupTopNav);

function openMobileMenu() {
  openPanel(navConfig);
}

function closeMobileMenu() {
  closePanel();
}

function setupTopNav() {
  if (breakpoint.matches) {
    // console.log('is mobile');
    modalNav.setAttribute('inert', '');
  } else {
    // console.log('is desktop');
    if (activePanel === navConfig) {
      closePanel();
    }
    modalNav.removeAttribute('inert');
  }
}

// function animateMenu() {
//   modalNav.classList.add('animating');

//   setTimeout(() => {
//     modalNav.classList.remove('animating');
//   }, 300);
// }

setupTopNav();

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

// Front-end mimicking initToasts and toast.html logic
function createToast(message, level = 'info') {
  const stack = document.querySelector('.toast-stack');
  if (!stack) return;

  const toast = document.createElement('div');
  toast.className = `toast toast--${level}`;
  toast.innerHTML = `
    <span class="toast__message">${message}</span>
    <button class="toast__close" aria-label="Dismiss notification">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="toast__icon" aria-hidden="true">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    </button>
  `;

  stack.appendChild(toast);

  const dismiss = () => {
    toast.classList.add('is-hiding');
    setTimeout(() => toast.remove(), 150);
  };

  toast
    .querySelector('.toast__close')
    .addEventListener('click', dismiss);

  setTimeout(dismiss, 4000);
}

// This grabs all toasts after page load (redirects/renders)
function initToasts() {
  document.querySelectorAll('.toast').forEach((toast) => {
    const closeBtn = toast.querySelector('.toast__close');

    const dismiss = () => {
      toast.classList.add('is-hiding');
      setTimeout(() => toast.remove(), 150);
    };

    closeBtn.addEventListener('click', dismiss);

    setTimeout(dismiss, 4000);
  });
}

initToasts();
