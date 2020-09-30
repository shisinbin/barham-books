from django.core.management.base import BaseCommand
from books.models import Book, Category
from taggit.models import Tag
from collections import Counter
from time import sleep
from books.choices import gen_fiction_tags, secondary_fiction_tags, non_fiction_tags, sci_fi_fantasy_tags, children_tags, teen_tags

class Command(BaseCommand):
    help = "Sort out tags"
    def handle(self, *args, **options):
        self.stdout.write("Sorting out tags")
        sleep(1)
        c = Counter()

        self.stdout.write("Moving tags to book_tags for every book")
        # for every tag in every book, copy tag to book_tags
        # and then clear all tags from book
        for bk in Book.objects.all():
            if bk.tags.all():
                for tag in bk.tags.all():
                    bk.book_tags.add(tag.name)
                bk.tags.clear()
                bk.save()
        self.stdout.write("Done...")
        sleep(1)
        self.stdout.write("Now putting tags in their bands")
        # add appropriate category for every book tag
        all_book_tags = Book.book_tags.all()
        if all_book_tags:
            for book_tag in all_book_tags:
                if book_tag.name in gen_fiction_tags:
                    book_tag.band = 1
                elif book_tag.name in secondary_fiction_tags:
                    book_tag.band = 2
                elif book_tag.name in non_fiction_tags:
                    book_tag.band = 3
                elif book_tag.name in sci_fi_fantasy_tags:
                    book_tag.band = 4
                elif book_tag.name in children_tags:
                    book_tag.band = 5
                elif book_tag.name in teen_tags:
                    book_tag.band = 6
                book_tag.save()
        self.stdout.write("Done that...")
        sleep(1)
        self.stdout.write("Now deleting the taggit tags that aren't associated to anything")

        # delete all the leftover taggit tags
        # should result in zero tags in the taggit admin area
        for taggit_tag in Tag.objects.all():
            if taggit_tag.taggit_taggeditem_items.count() == 0:
                print('removing: {}'.format(taggit_tag.name))
                taggit_tag.delete()
            else:
                print('keeping: {}'.format(taggit_tag.name))
        self.stdout.write("Finito")