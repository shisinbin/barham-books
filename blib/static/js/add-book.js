document.addEventListener('DOMContentLoaded', function () {
  document
    .getElementById('clear-photo')
    .addEventListener('click', function () {
      const input = document.getElementById('id_photo');
      if (!input) return;
      input.value = '';
    });

  $(function () {
    $('.js-book-tags').select2({
      placeholder: 'Select book tags',
      width: '100%',
      allowClear: true,
    });

    $('.js-existing-series').select2({
      placeholder: 'Select existing series',
      width: '100%',
      allowClear: true,
    });
  });
});
