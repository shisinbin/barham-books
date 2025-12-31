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
