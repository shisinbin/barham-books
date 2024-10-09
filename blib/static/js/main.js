setTimeout(function () {
  $('#message').fadeOut('slow');
}, 3000);

// $(function () {
//   $('#keywords').autocomplete({
//     source: function (request, response) {
//       $.ajax({
//         url: "{% url 'autocomplete_books' %}",
//         data: {
//           term: request.term,
//         },
//         success: function (data) {
//           response(data);
//         },
//       });
//     },
//     minLength: 3, // Minimum length for autocomplete to start
//     select: function (event, ui) {
//       if (ui.item.url) {
//         window.location.href = ui.item.url; // Redirect to the book's URL on selection
//       }
//     },
//   });
// });
