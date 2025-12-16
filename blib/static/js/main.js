// setTimeout(function () {
//   $('.js-alert').fadeOut('slow');
// }, 3000);

setTimeout(() => {
  document.querySelectorAll('.js-alert').forEach((alert) => {
    alert.style.transition = 'opacity 0.5s';
    alert.style.opacity = '0';
    setTimeout(() => alert.remove(), 500);
  });
}, 3000);
