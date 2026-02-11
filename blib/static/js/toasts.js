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
