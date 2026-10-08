import requests
from django.conf import settings

# OPENLIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"

# def search_openlibrary(*, isbn=None, title=None, author=None, limit=10):
#     params = {"limit": limit}
    
#     if isbn:
#         params["isbn"] = isbn
#     if title:
#         params["title"] = title
#     if author:
#         params["author"] = author
    
#     response = requests.get(OPENLIBRARY_SEARCH_URL, params=params, timeout=10)
#     response.raise_for_status()

#     return response.json()

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"

def google_books_request(query, *, max_results=5):
    params = {
        "q": query,
        "maxResults": max_results,
        "key": settings.GOOGLE_BOOKS_API_KEY,
    }

    resp = requests.get(
        GOOGLE_BOOKS_URL,
        params=params,
        timeout=10,
    )
    resp.raise_for_status()

    return resp.json()


def search_google_books(*, isbn=None, title=None, author=None, max_results=5):
    """
    Search Google Books.

    First tries the more precise Google Books query syntax.
    If that returns no items for a title/author search, falls back to
    a plain text query because intitle:/inauthor: can be unreliable.
    """
    fallback_q = None

    if isbn:
        q = f"isbn:{isbn}"
    else:
        restricted_parts = []
        plain_parts = []

        if title:
            restricted_parts.append(f'intitle:"{title}"')
            plain_parts.append(title)

        if author:
            restricted_parts.append(f'inauthor:"{author}"')
            plain_parts.append(author)

        q = " ".join(restricted_parts)
        fallback_q = " ".join(plain_parts)

    data = google_books_request(q, max_results=max_results)

    if data.get("items"):
        return data
    
    if fallback_q and fallback_q != q:
        return google_books_request(fallback_q, max_results=max_results)
    
    return data
