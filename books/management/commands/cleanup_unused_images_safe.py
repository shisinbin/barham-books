import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from books.models import Book


log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename="logs/deleted_unused_images.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Command(BaseCommand):
    help = "Clean up unused images in the media/books folder"

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Actually delete unused files. Without this, the command only reports what would be deleted.",
        )

    def handle(self, *args, **options):
        should_delete = options["delete"]

        if should_delete:
            self.stdout.write(self.style.WARNING("Delete mode enabled. Files will be removed."))
        else:
            self.stdout.write(self.style.WARNING("Dry run only. No files will be deleted."))

        used_files = set(
            Book.objects
            .exclude(photo="")
            .values_list("photo", flat=True)
        )

        self.stdout.write(f"Used book images in database: {len(used_files)}")

        used_thumbnails = set()
        for file in used_files:
            base, ext = os.path.splitext(file)
            used_thumbnails.add(f"{base}{ext}.100x0_q85{ext}")

        media_books_path = os.path.join(settings.MEDIA_ROOT, "books")

        if not os.path.exists(media_books_path):
            self.stdout.write(self.style.WARNING(f"Folder does not exist: {media_books_path}"))
            return

        total_files = 0
        unused_files = 0
        deleted_files = 0

        for root, _, files in os.walk(media_books_path):
            for filename in files:
                total_files += 1

                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, settings.MEDIA_ROOT)

                if relative_path in used_files or relative_path in used_thumbnails:
                    continue

                unused_files += 1

                if should_delete:
                    logging.info(f"Deleted: '{relative_path}'")
                    os.remove(full_path)
                    deleted_files += 1
                else:
                    self.stdout.write(f"Would delete: {relative_path}")

        self.stdout.write(f"Total files in media/books: {total_files}")
        self.stdout.write(f"Unused files found: {unused_files}")

        if should_delete:
            self.stdout.write(self.style.SUCCESS(f"Unused files deleted: {deleted_files}"))
        else:
            self.stdout.write(self.style.WARNING("Dry run complete. Re-run with --delete to remove files."))