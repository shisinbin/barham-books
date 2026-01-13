// document.getElementById('current-year').textContent =
//   new Date().getFullYear();

const main = document.querySelector('#main');
const footer = document.querySelector('#footer');
const header = document.querySelector('#header');
const btnOpen = document.querySelector('#btnOpen');
const btnClose = document.querySelector('#btnClose');
const menuTopNav = document.querySelector('#menuTopNav');
const breakpoint = window.matchMedia('(width < 600px)');

const inertable = [
  main,
  footer,
  document.querySelector('.topnav__homelink'),
  btnOpen,
  document.querySelector('#skip-header-link'),
];

let isMenuOpen = false;

btnOpen.addEventListener('click', openMobileMenu);
btnClose.addEventListener('click', closeMobileMenu);
breakpoint.addEventListener('change', setupTopNav);

function openMobileMenu() {
  if (isMenuOpen) return;
  isMenuOpen = true;

  animateMenu();

  header.classList.add('is-open');
  btnOpen.setAttribute('aria-expanded', 'true');
  menuTopNav.removeAttribute('inert');

  setInertAll(true);

  bodyScrollLockUpgrade.disableBodyScroll(menuTopNav);
  attachGlobalMenuListeners();

  btnClose.focus();
}

function closeMobileMenu() {
  if (!isMenuOpen) return;
  isMenuOpen = false;

  animateMenu();

  header.classList.remove('is-open');
  btnOpen.setAttribute('aria-expanded', 'false');
  menuTopNav.setAttribute('inert', '');

  setInertAll(false);

  bodyScrollLockUpgrade.enableBodyScroll(menuTopNav);
  detachGlobalMenuListeners();

  btnOpen.focus();
}

function setupTopNav() {
  if (breakpoint.matches) {
    // console.log('is mobile');
    menuTopNav.setAttribute('inert', '');
  } else {
    // console.log('is desktop');
    if (isMenuOpen) {
      closeMobileMenu();
    }
    menuTopNav.removeAttribute('inert');
  }
}

function animateMenu() {
  menuTopNav.classList.add('animating');

  setTimeout(() => {
    menuTopNav.classList.remove('animating');
  }, 300);
}

function handleKeydown(e) {
  if (!isMenuOpen) return;

  if (e.key === 'Escape') {
    e.preventDefault();
    closeMobileMenu();
  }
}

function handleClickOutside(e) {
  if (!isMenuOpen) return;

  if (!menuTopNav.contains(e.target) && !btnOpen.contains(e.target)) {
    closeMobileMenu();
  }
}

function attachGlobalMenuListeners() {
  document.addEventListener('keydown', handleKeydown);
  document.addEventListener('click', handleClickOutside);
}

function detachGlobalMenuListeners() {
  document.removeEventListener('keydown', handleKeydown);
  document.removeEventListener('click', handleClickOutside);
}

function setInertAll(state) {
  inertable.forEach((el) => {
    if (!el) return;
    state
      ? el.setAttribute('inert', '')
      : el.removeAttribute('inert');
  });
}

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

  const trap = focusTrap.createFocusTrap(menuTopNav, {
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
