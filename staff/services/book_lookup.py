import requests
from django.conf import settings

OPENLIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"

def search_openlibrary(*, isbn=None, title=None, author=None, limit=10):
    params = {"limit": limit}
    
    if isbn:
        params["isbn"] = isbn
    if title:
        params["title"] = title
    if author:
        params["author"] = author
    
    response = requests.get(OPENLIBRARY_SEARCH_URL, params=params, timeout=10)
    response.raise_for_status()

    return response.json()


def search_google_books(*, isbn=None, title=None, author=None, max_results=5):
    if isbn:
        q = f"isbn:{isbn}"
    else:
        parts = []
        if title:
            parts.append(f'intitle:"{title}"')
        if author:
            parts.append(f'inauthor:"{author}"')
        q = " ".join(parts)

    params = {
        "q": q,
        "maxResults": max_results,
        "key": settings.GOOGLE_BOOKS_API_KEY,
    }

    resp = requests.get(
        "https://www.googleapis.com/books/v1/volumes",
        params=params,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
