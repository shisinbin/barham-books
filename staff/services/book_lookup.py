import requests

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