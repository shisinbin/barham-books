document
  .getElementById('clear-photo')
  .addEventListener('click', function () {
    const input = document.getElementById('id_photo');
    if (!input) return;
    input.value = '';
  });
