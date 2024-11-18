import logging
import os
from django.core.management.base import BaseCommand
from books.models import Book
from books.views import format_book_title

log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(filename='logs/formatted_titles.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class Command(BaseCommand):
  help = 'Format all book titles in the database for consistency.'

  def handle(self, *args, **kwargs):
    self.stdout.write('Starting the formatting process...')
    updated_count = 0
    skipped_count = 0

    suffixes = (', The', ', A', ', An')

    for book in Book.objects.all():
      original_title = book.title

      title_to_send_to_helper = original_title
      
      for suffix in suffixes:
        if original_title.endswith(suffix):
          article = suffix[2:]
          title_without_suffix = original_title[:-len(suffix)].strip()
          title_to_send_to_helper = f"{article} {title_without_suffix}"
          break

      formatted_title = format_book_title(title_to_send_to_helper)

      if original_title == formatted_title:
        skipped_count += 1
        # self.stdout.write(f"Skipping this book: {original_title}")
        continue

      # book.title = formatted_title
      # book.save()
      # self.stdout.write(f"Making a change here! Old title: {original_title}, new title: {formatted_title}")
      updated_count += 1

      logging.info(f"Updated: '{original_title} -> '{formatted_title}'")

    self.stdout.write(f"Formatting complete. Updated: {updated_count}, Skipped: {skipped_count}")