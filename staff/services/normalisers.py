from staff.helpers import extract_isbns_from_ia

def normalise_openlibrary_results(data):
    results = []

    for doc in data.get("docs", []):
        isbns = extract_isbns_from_ia(doc.get("ia", []))
        cover_id = doc.get("cover_i")
        author_list = doc.get("author_name", [])

        results.append({
            "source": "openlibrary",
            "title": doc.get("title"),
            "author": author_list[0] if author_list else None,
            "isbns": isbns,
            "year": doc.get("first_publish_year"),
            "cover_url": (
                f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                if cover_id else None
            ),
        })
    
    return results

def normalise_google_books_results(data):
    """
    Normalise Google Books API results into a predictable structure.
    """
    results = []

    items = data.get("items", [])
    if not isinstance(items, list):
        return results

    for item in items:
        if not isinstance(item, dict):
            continue

        volume_id = item.get("id")
        volume_info = item.get("volumeInfo", {})

        if not volume_id or not isinstance(volume_info, dict):
            continue

        # --- Title / subtitle ---
        title = volume_info.get("title")
        subtitle = volume_info.get("subtitle")

        # if title and subtitle:
        #     full_title = f"{title}: {subtitle}"
        # else:
        #     full_title = title

        # --- Authors ---
        authors = volume_info.get("authors") or []
        if not isinstance(authors, list):
            authors = []

        # --- Description ---
        description = volume_info.get("description")

        # --- Published year ---
        published_date = volume_info.get("publishedDate")
        published_year = None
        if isinstance(published_date, str) and len(published_date) >= 4:
            year_part = published_date[:4]
            if year_part.isdigit():
                published_year = int(year_part)

        # --- Publisher ---
        publisher = volume_info.get("publisher")

        # --- Page count ---
        page_count = volume_info.get("pageCount")
        if not isinstance(page_count, int) or page_count <= 0:
            page_count = None

        # --- ISBNs ---
        isbn10 = None
        isbn13 = None

        for ident in volume_info.get("industryIdentifiers", []):
            if not isinstance(ident, dict):
                continue
            if ident.get("type") == "ISBN_10":
                isbn10 = ident.get("identifier")
            elif ident.get("type") == "ISBN_13":
                isbn13 = ident.get("identifier")

        # --- Categories ---
        categories = volume_info.get("categories") or []
        if not isinstance(categories, list):
            categories = []

        # --- Thumbnail ---
        image_links = volume_info.get("imageLinks") or {}
        thumbnail = image_links.get("thumbnail")

        results.append({
            "source": "google_books",
            "volume_id": volume_id,
            "title": title,
            "subtitle": subtitle, # not using yet
            "authors": authors, # will only use first
            "description": description,
            "published_year": published_year,
            "publisher": publisher,
            "page_count": page_count,
            "isbn10": isbn10,
            "isbn13": isbn13,
            "categories": categories,
            "thumbnail": thumbnail,
        })

    return results
