from django.core.management.base import BaseCommand
import csv
from books.models import Book, BookInstance2
from collections import Counter
from time import sleep

class Command(BaseCommand):
    help = "Sort out years"
    def add_arguments(self, parser):
        parser.add_argument("csvfile", type=open)
    def handle(self, *args, **options):

        self.stdout.write("Sorting out years, wish me luck")
        sleep(1)

        c= Counter()

        reader = csv.DictReader(options.pop("csvfile"))
        for row in reader:

            c["csv rows"] +=1

            # grab the isbn and year in right format
            isbn = row['isbn13']
            year = row['year']

            if year:
                year = int(year)
                if year < 0:
                    year = None

            # check to see we have values in both columns
            if year and isbn:

                c["good rows"] +=1

                # try and find an instance with this isbn
                try:
                    instance = BookInstance2.objects.filter(isbn13=isbn).first()

                    if instance:

                        # check if book doesn't already have a value in year field
                        if instance.book.year is None:
                            instance.book.year = year
                            instance.book.save()
                            c["changes made"] +=1
                except:
                    pass

        self.stdout.write(
            "Total CSV rows=%d, of those having both isbn and year=%d. Total changes made=%d."
            % (c["csv rows"], c["good rows"], c["changes made"])
        )