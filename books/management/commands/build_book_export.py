import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from books.export_utils import write_books_csv

class Command(BaseCommand):
    help = "Build the public Barham Books catalogue CSV export."

    def add_arguments(self, parser):
        parser.add_argument(
            "--site-url",
            default="",
            help="Optional absolute site URL, e.g. https://barhamlibrary.xyz",
        )

    def handle(self, *args, **options):
        export_root = Path(settings.PRIVATE_EXPORT_ROOT)
        export_root.mkdir(parents=True, exist_ok=True)

        csv_path = export_root / settings.BOOK_EXPORT_FILENAME
        metadata_path = export_root / settings.BOOK_EXPORT_METADATA_FILENAME

        with csv_path.open("w", newline="", encoding="utf-8") as file_obj:
            row_count = write_books_csv(
                file_obj,
                site_url=options["site_url"],
            )

        metadata = {
            "filename": settings.BOOK_EXPORT_FILENAME,
            "generated_at": timezone.now().isoformat(),
            "row_count": row_count,
            "format": "csv",
        }

        metadata_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {row_count} books to {csv_path}"
            )
        )