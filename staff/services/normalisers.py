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