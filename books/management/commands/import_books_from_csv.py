from django.core.management.base import BaseCommand
import csv
from collections import Counter
from books.models import Book, BookInstance2
from authors.models import Author
from datetime import datetime
from django.core.files.images import ImageFile
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import os.path
from urllib import request
from django.core.files.base import ContentFile

# class Command(BaseCommand):
#     help = "Import books"
#     def add_arguments(self, parser):
#         parser.add_argument("csvfile", type=open)
#         # trying to add an image now
#         parser.add_argument("image_basedir", type=str)
#     def handle(self, *args, **options):
#         self.stdout.write("Importing books")
#         c = Counter()
#         reader = csv.DictReader(options.pop("csvfile"))
#         for row in reader:
#             author, created_author = Author.objects.get_or_create(
#                 first_name=row["first_name"], last_name=row["last_name"]
#             )
#             c["authors"] += 1
#             if created_author:
#                 c["authors_created"] += 1
#                 author.save() # putting this here so that it doesn't save it every time, saving processing?

#             book, created_book = Book.objects.get_or_create(
#                 title=row["title"], author=author
#                 )
#             c["books"] += 1

#             if created_book:
#                 book.summary = row["description"]
#                 book.publish_date = datetime.strptime(row["publish_date"], "%Y-%m-%d").date()
#                 book.isbn = row["isbn"]
#                 # and add any other book detals
#                 c["books_created"] += 1
#                 # also figure out a split thingy to get other_authors if there are any
#                 book.save() # again adding this here to save on processing

#             try:
#                 with open(os.path.join(
#                                 options["image_basedir"],
#                                 row["image_filename"],
#                             ),
#                           "rb",) as f:
#                     book.photo = ImageFile(f)
#                     book.save()
#                     c["images"] += 1
#             except:
#                 pass

#             # new_instance = BookInstance2.objects.create(
#             #     book=book, publisher=row["publisher"], pages=row["pages"]
#             # ) # maybe also put the isbn10 and isbn13 numbers here

#             # c["instances_created"] += 1
#             # new_instance.save()
#         self.stdout.write(
#             "Books processed=%d (created=%d, images=%d)"
#             % (c["books"], c["books_created"], c["images"])
#         )
#         self.stdout.write(
#             "Authors processed=%d (created=%d)"
#             % (c["authors"], c["authors_created"])
#         )
#         self.stdout.write("Instances created=%d" % c["instances_created"])


class Command(BaseCommand):
    help = "Import books"
    def add_arguments(self, parser):
        parser.add_argument("csvfile", type=open)
        # trying to add an image now
        parser.add_argument("image_basedir", type=str)
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
                if row["middle_name"]:
                    c["middle_name"] += 1
                    author.middle_name = row["middle_name"]
                c["authors_created"] += 1
                author.save() # putting this here so that it doesn't save it every time, saving processing?

            book, created_book = Book.objects.get_or_create(
                title=row["title"], author=author
                )
            c["books"] += 1

            if created_book:
                book.summary = row["description"]
                book.publish_date = datetime.strptime(row["publish_date"], "%Y-%m-%d").date()
                book.tags.add('sci-fi')
                book.user_tags.add('star trek')

                if row["other_authors"]:
                    book.other_authors = row["other_authors"]

                c["books_created"] += 1
                book.save() # again adding this here to save on processing

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

                if row["isbn13"]:
                    isbn = row["isbn13"]
                elif row["isbn10"]:
                    isbn = row["isbn10"]
                else:
                    isbn = None

                if isbn:
                    image_url = 'http://covers.openlibrary.org/b/isbn/' + isbn + '.jpg'
                    response = request.urlopen(image_url)
                    try:
                        book.photo.save('temp.jpg',
                                    ContentFile(response.read()),
                                    save=False)
                        book.save()
                    except:
                        print('something went wrong')

            # maybe think of a better way of duplicating data for a copy of an instance.
            # I think another model where you put all the static info might work.
            # but might be another way - vaguely remember something in django by ex 3 bk
            for i in range(int(row["copies"])):
                new_instance = BookInstance2.objects.create(
                                                    book=book,
                                                    publisher=row["publisher"],
                                                    pages=row["pages"],
                                                    isbn10=row["isbn10"],
                                                    isbn13=row["isbn13"],
                )
                c["instances_created"] += 1
                new_instance.save()

        self.stdout.write(
            "Books processed=%d (created=%d, images=%d)"
            % (c["books"], c["books_created"], c["images"])
        )
        self.stdout.write(
            "Authors processed=%d (created=%d)"
            % (c["authors"], c["authors_created"])
        )
        self.stdout.write("Instances created=%d" % c["instances_created"])