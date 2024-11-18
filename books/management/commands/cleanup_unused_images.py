import logging
from django.core.management.base import BaseCommand
import os
from django.conf import settings
from books.models import Book

log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(filename='logs/deleted_unused_images.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class Command(BaseCommand):
  help = 'Clean up unused images and thumbnails in the media/books folder'

  def handle(self, *args, **options):
    self.stdout.write('Starting cleanup of unused images...')


    # 1 Collect all used filenames
    used_files = set()
    total_books_with_images = 0
    for book in Book.objects.exclude(photo='').only('photo'):
      used_files.add(book.photo.name)
      total_books_with_images += 1
    self.stdout.write(f"Used images: {len(used_files)}")

    # 2 Collect associated thumbnails
    used_thumbnails = set()
    for file in used_files:
      base, ext = os.path.splitext(file)
      used_thumbnails.add(f"{base}{ext}.100x0_q85{ext}")
    self.stdout.write(f"Generated thumbnails: {len(used_thumbnails)}")

    # Iterate through every books media folder
    media_books_path = os.path.join(settings.MEDIA_ROOT, 'books')
    total_images = 0
    deleted_files = 0
    for root, _, files in os.walk(media_books_path):
      for filename in files:
        total_images += 1
        full_path = os.path.join(root, filename)
        relative_path = os.path.relpath(full_path, settings.MEDIA_ROOT)

        if relative_path not in used_files and relative_path not in used_thumbnails:
          logging.info(f"Deleted: '{relative_path}'")
          os.remove(full_path)
          deleted_files += 1

    self.stdout.write(f"Total books with associated images: {total_books_with_images}")
    self.stdout.write(f"Total images in 'books' folder: {total_images}")
    self.stdout.write(f"Total unused images deleted: {deleted_files}")
    self.stdout.write('Cleanup complete.')