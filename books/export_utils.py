import csv

from django.conf import settings
from django.urls import reverse

from .models import Book

BOOK_EXPORT_HEADERS = [
    "book_id",
    "title",
    "author",
    "other_authors",
    "summary",
    "tags",
    "original_publication_year",
    "category",
    "series",
    "series_number",
    # "language",
    "book_url",
    # "copy_count",
]

def get_book_export_queryset():
    return (
        Book.objects
        .select_related("author", "category", "series")
        .prefetch_related("book_tags")
        .order_by("title", "author__last_name", "author__first_name")
    )

def get_absolute_book_url(book, site_url=None):
    path = book.get_absolute_url()

    if site_url:
        return f"{site_url.rstrip('/')}{path}"
    
    return path

def write_books_csv(file_obj, site_url=None):
    writer = csv.writer(file_obj)
    writer.writerow(BOOK_EXPORT_HEADERS)

    row_count = 0

    for book in get_book_export_queryset():
        tags = ", ".join(
            tag.name for tag in book.book_tags.all().order_by("band", "name")
        )

        writer.writerow([
            book.id,
            book.title,
            str(book.author) if book.author else "",
            book.other_authors,
            book.summary,
            tags,
            book.year or "",
            book.category.name if book.category else "",
            book.series.name if book.series else "",
            book.series_num or "",
            # book.language,
            get_absolute_book_url(book, site_url=site_url),
            # book.instances.count(),
        ])

        row_count += 1

    return row_count