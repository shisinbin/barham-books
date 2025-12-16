/*
  CSRF handled once, globally
*/

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');

    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(
          cookie.slice(name.length + 1)
        );
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');
