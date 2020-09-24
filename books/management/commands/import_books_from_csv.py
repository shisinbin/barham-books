from django.core.management.base import BaseCommand
import csv
from collections import Counter
from books.models import Book, BookInstance2, Series
from authors.models import Author
from datetime import datetime
from django.core.files.images import ImageFile
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import os.path
from urllib import request
from django.core.files.base import ContentFile
import os

class Command(BaseCommand):
    help = "Import books"
    def add_arguments(self, parser):
        parser.add_argument("csvfile", type=open)
        ####################################################
        # Adding another argument to specify from what directory
        # images are to be added. Now not used, so commented out
        #####################################################
        # parser.add_argument("image_basedir", type=str)
    def handle(self, *args, **options):
        self.stdout.write("Importing books")
        c = Counter()
        reader = csv.DictReader(options.pop("csvfile"))
        for row in reader:
            author, created_author = Author.objects.get_or_create(
                first_name=row["first_name"],
                #middle_name=row["middle_name"],
                last_name=row["last_name"]
            )
            c["authors"] += 1
            if created_author:
                #############################
                # commenting out middle names
                ############################
                # if row["middle_name"]:
                #     c["middle_name"] += 1
                #     author.middle_names = row["middle_name"]
                c["authors_created"] += 1
                author.save() # putting this here so that it doesn't save it every time, saving processing?

            book, created_book = Book.objects.get_or_create(
                title=row["title"], author=author
                )
            c["books"] += 1

            if created_book:
                book.summary = row["description"]

                if row["publish_date"]:
                    book.publish_date = datetime.strptime(row["publish_date"], "%Y-%m-%d").date()
                
                if row["tags"]:
                    tags = row["tags"].split(',')
                    for tag in tags:
                        c["tags_added"] +=1
                        book.tags.add(tag.strip())

                if row["other_authors"]:
                    book.other_authors = row["other_authors"]

                if row["series"]:
                    series, created_series = Series.objects.get_or_create(
                        name=row["series"])
                    if created_series:
                        c["series_created"] += 1
                    book.series = series
                    if row["series_num"]:
                        book.series_num = row["series_num"]
                        c["series_added"]

                c["books_created"] += 1
                book.save() # again adding this here to save on processing

                ################################################
                # Saving images approach where images are saved in
                # specified directory, would work but chose
                # another way
                ################################################
                # try:
                #     with open(os.path.join(
                #                     options["image_basedir"],
                #                     row["image_filename"],
                #                 ),
                #               "rb",) as f:
                #         book.photo = ImageFile(f)
                #         book.save()
                #         c["images"] += 1
                # except:
                #     pass

                ###############################################
                # the second approach for saving images from
                # openlibrary. Did work, and was used, but their
                # images are inconsistent in terms of quality
                # so going to add manually, one by one
                ################################################
                # if row["isbn13"]:
                #     isbn_for_lookup = row["isbn13"]
                # elif row["isbn10"]:
                #     isbn_for_lookup = row["isbn10"]
                # else:
                #     isbn_for_lookup = None
                #
                # if isbn_for_lookup:
                #     image_url = 'http://covers.openlibrary.org/b/isbn/' + isbn_for_lookup + '.jpg'
                #     response = request.urlopen(image_url)
                #     try:
                #         image_file = ContentFile(response.read())
                #         if image_file.size > 1000:
                #             book.photo.save('temp.jpg',
                #                         image_file,
                #                         save=False)
                #             c["images"] += 1
                #             book.save()
                #     except:
                #         print('something went wrong')

            # maybe think of a better way of duplicating data for a copy of an instance.
            # I think another model where you put all the static info might work.
            # but might be another way - vaguely remember something in django by ex 3 bk
            for i in range(int(row["copies"])):
                if row["pages"]:
                    pages = int(row["pages"])
                else:
                    pages = None

                if row["isbn13"]:
                    if len(row["isbn13"]) <14:
                        isbn13 = row["isbn13"]
                    else:
                        isbn13 = None
                else:
                    isbn13 = None
                
                if row["isbn10"]:
                    if len(row["isbn10"]) <11:
                        isbn10 = row["isbn10"]
                    else:
                        isbn10 = None
                else:
                    isbn10 = None
                    
                new_instance = BookInstance2.objects.create(
                                                    book=book,
                                                    publisher=row["publisher"],
                                                    pages=pages,
                                                    isbn10=isbn10,
                                                    isbn13=isbn13,
                )
                c["instances_created"] += 1
                new_instance.save()

        self.stdout.write(
            "Books processed=%d (created=%d, images=%d, tags=%d)"
            % (c["books"], c["books_created"], c["images"], c["tags_added"])
        )
        self.stdout.write(
            "Authors processed=%d (created=%d)"
            % (c["authors"], c["authors_created"])
        )
        self.stdout.write("Instances created=%d" % c["instances_created"])
        self.stdout.write(
            "Series created=%d (added=%d)"
            % (c["series_created"], c["series_added"])
        )