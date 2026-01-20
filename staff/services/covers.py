import requests
import re

def build_cover_candidates(book, *, max_results=3, logger=None):
    """
    Given a Book instance, return an ordered list of plausible
    OpenLibrary cover image candidates.

    Returns: list of dicts like:
    {
        "url": str,
        "source": "cover_i" | "olid" | "isbn10" | "isbn13",
        "result_rank": int | None,
    }
    """
    BASE = "https://covers.openlibrary.org/b"

    def _log(msg):
        if logger:
            logger.info(msg)

    def _normalise_isbn(isbn):
        if not isbn:
            return None
        s = isbn.replace("-", "").strip().upper()
        if not s.isdigit():
            return None
        if len(s) not in (10, 13):
            return None
        return s

    def _dedupe(seq):
        seen = set()
        out = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    def _normalise_title(t):
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', t).lower()

        keywords = [
            word for word in clean_title.split()
            if word not in {'the', 'and'} and len(word) >= 3
        ]

        return " ".join(keywords)

    title = _normalise_title(book.title or "")

    author_name = None
    if book.author:
        author_name = f"{book.author.first_name} {book.author.last_name}".strip()

    isbn10s = []
    isbn13s = []

    for inst in book.instances.all():
        norm10 = _normalise_isbn(inst.isbn10)
        norm13 = _normalise_isbn(inst.isbn13)

        if norm10:
            isbn10s.append(norm10)
        if norm13:
            isbn13s.append(norm13)

    isbn10s = _dedupe(isbn10s)
    isbn13s = _dedupe(isbn13s)

    _log(f"title={title!r}, author={author_name!r}")
    _log(f"ISBN10s={isbn10s}, ISBN13s={isbn13s}")

    search_results = []

    if title and author_name:
        try:
            resp = requests.get(
                "https://openlibrary.org/search.json",
                params={"title": title, "author": author_name},
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json()

            docs = data.get("docs", [])
            if isinstance(docs, list):
                search_results = docs[:max_results]
            else:
                _log("OpenLibrary returned non-list docs")

        except requests.RequestException as exc:
            _log(f"OpenLibrary request failed: {exc}")
        except ValueError:
            _log("OpenLibrary returned invalid JSON")

    candidates = []

    for rank, doc in enumerate(search_results, start=1):
        if not isinstance(doc, dict):
            continue

        cover_i = doc.get("cover_i")
        if isinstance(cover_i, int):
            candidates.append({
                "url": f"{BASE}/id/{cover_i}-L.jpg",
                "source": "cover_i",
                "priority": 1,
                "result_rank": rank,
            })

        olid = doc.get("cover_edition_key")
        if isinstance(olid, str) and olid.strip():
            candidates.append({
                "url": f"{BASE}/olid/{olid.strip()}-L.jpg",
                "source": "olid",
                "priority": 2,
                "result_rank": rank,
            })

    for isbn in isbn13s:
        candidates.append({
            "url": f"{BASE}/isbn/{isbn}-L.jpg",
            "source": "isbn13",
            "priority": 3,
            "result_rank": None,
        })

    for isbn in isbn10s:
        candidates.append({
            "url": f"{BASE}/isbn/{isbn}-L.jpg",
            "source": "isbn10",
            "priority": 4,
            "result_rank": None,
        })

    seen_urls = set()
    unique = []

    for item in candidates:
        url = item["url"]
        if url not in seen_urls:
            seen_urls.add(url)
            unique.append(item)

    _log(f"Generated {len(unique)} unique cover candidates")

    return unique[:15]
