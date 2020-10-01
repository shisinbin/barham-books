from django.core.management.base import BaseCommand
from books.models import Book, Category
from taggit.models import Tag
from collections import Counter
from time import sleep

class Command(BaseCommand):
    help = "Sort out categories"
    def handle(self, *args, **options):
        self.stdout.write("Sorting out categories, wish me luck")
        sleep(1)
        c = Counter()

        # fetch all books
        queryset = Book.objects.all()
        self.stdout.write("There are " + str(len(queryset)) + " books total to deal with, oh vey!")
        sleep(1)
        
        # actually ADD the categories

        # if there are no categories
        if not Category.objects.all():
            self.stdout.write("There are no categories, so adding them all...")
            sleep(1)
            gen_cat = Category.objects.create(
                name='General fiction',
                short_name='General fiction',
                code='GEN',
                order=1,
                description='General Fiction, sometimes called contemporary fiction, focuses on the everyday experiences and conflicts of a protagonist, usually an adult, with detailed characterization and background. General Fiction is intended for older readers and has more mature themes.',
                tags_included=[]
            )
            gen_cat.save()
            self.stdout.write("Added General Fiction category!")
            sleep(1)

            non_cat = Category.objects.create(
                name='Non-fiction',
                short_name='Non-fiction',
                code='NON',
                order=2,
                description='Non-Fiction is writing that focuses on real events, people, and experiences. The genre includes (but is not limited to) memoirs, travelogues, biographies, and business advice.',
                tags_included=[]
            )
            non_cat.save()
            self.stdout.write("Added Non-Fiction category!")
            sleep(1)

            sff_cat = Category.objects.create(
                name='Sci-Fi and Fantasy',
                short_name='Sci-Fi & Fantasy',
                code='SFF',
                order=3,
                description='Science Fiction typically revolves around a futuristic or space-age world wherein imaginative scientific and technological innovations are possible within the story’s established laws of nature. Science Fiction deals with the consequences and impact of science (actual or imagined) on individual and societal levels, and often includes advanced devices, such as time-machines, or other life forms, such as aliens.',
                tags_included=[]
            )
            sff_cat.save()
            self.stdout.write("Added Sci-Fi and Fantasy category!")
            sleep(1)

            childrens_cat = Category.objects.create(
                name="Children's to Middle Grade",
                short_name="Children's & MG",
                code='CHI',
                order=4,
                description='Middle-grade fiction refers to books written for readers between the ages of 8 and 12.',
                tags_included=[]
            )
            childrens_cat.save()
            self.stdout.write("Added Children and Middle Grade category!")
            sleep(1)

            ya_cat = Category.objects.create(
                name='Teen to Young Adult',
                short_name='Teen & YA',
                code='TYA',
                order=5,
                description='Teen Fiction traces the ins, outs, ups and downs of growing up through the emotional, physical, and social experiences of a teenaged or young adult protagonist with which readers identify. Teen Fiction often takes place within a high school setting and may serve as a “coming-of-age” story, documenting the awkwardness of adolescence and the challenge of coping with difficult social issues.',
                tags_included=[]
            )
            ya_cat.save()
            self.stdout.write("Added Teen and YA category!")
            sleep(1)

        else:
            # fetch all the categories
            self.stdout.write("Fetching all FIVE categories")
            sleep(1)
            childrens_cat = Category.objects.get(code='CHI')
            ya_cat = Category.objects.get(code='TYA')
            sff_cat = Category.objects.get(code='SFF')
            non_cat = Category.objects.get(code='NON')
            gen_cat = Category.objects.get(code='GEN')


        # CHI - children's to middle grade:
        self.stdout.write("Dealing with Children first...")
        sleep(1)
        queryset_children = Book.objects.filter(category__isnull=True, book_tags__name__in=["children's", "middle grade"]).distinct()
        if queryset_children:
            for childrens_book in queryset_children:
                is_children = True
                for tag in childrens_book.book_tags.all():
                    if tag.name == "young adult" or tag.name == "teen":
                        is_children = False
                        break
                if is_children:
                    childrens_book.category = childrens_cat
                    childrens_book.save()
                    c["children_categorised"] += 1
                    c["total_processed"] += 1
        else:
            self.stdout.write("No childrens books to categorise.")

        # Teens to Young Adults - catches all books that could be considered children's AS WELL as teen/ya
        self.stdout.write("Now teens and YA...")
        sleep(1)
        queryset_ya = Book.objects.filter(category__isnull=True, book_tags__name__in=["young adult", "teen"]).distinct()
        if queryset_ya:
            for ya_book in queryset_ya:
                ya_book.category = ya_cat
                ya_book.save()
                c["ya_categorised"] += 1
                c["total_processed"] += 1
        else:
            self.stdout.write("No YA books to categorise.")

        # Sci-Fi/Fantasy
        self.stdout.write("It's Sci-Fi and Fantasy next...")
        sleep(1)
        queryset_sff = Book.objects.filter(category__isnull=True, book_tags__name__in=["sci-fi", "fantasy"]).distinct()
        if queryset_sff:
            for sff_book in queryset_sff:
                sff_book.category = sff_cat
                sff_book.save()
                c["sff_categorised"] += 1
                c["total_processed"] += 1
        else:
            self.stdout.write("No Sci-Fi/Fantasy books to categorise")

        # Non-fiction
        self.stdout.write("Let's get them non-fiction books out da way...")
        sleep(1)
        queryset_non = Book.objects.filter(category__isnull=True, book_tags__name__in=["non-fiction", "memoir"]).distinct()
        if queryset_non:
            for non_book in queryset_non:
                non_book.category = non_cat
                non_book.save()
                c["non_categorised"] += 1
                c["total_processed"] += 1
        else:
            self.stdout.write("No non-fiction books to categorise")

        # General, effectively the rest
        self.stdout.write("Last one, it's a biggie, Gen Fiction...")
        sleep(1)
        queryset_gen = Book.objects.filter(category__isnull=True).distinct()
        if queryset_gen:
            for gen_book in queryset_gen:
                gen_book.category = gen_cat
                gen_book.save()
                c["gen_categorised"] += 1
                c["total_processed"] += 1
        else:
            self.stdout.write("No General fiction books to categorise.")



        sleep(3)

        self.stdout.write("Books processed = %d" % c["total_processed"])
        self.stdout.write("Childrens = %d" % c["children_categorised"])
        self.stdout.write("Teen/Young adult = %d" % c["ya_categorised"])
        self.stdout.write("Sci-Fi/Fantasy = %d" % c["sff_categorised"])
        self.stdout.write("Non-fiction = %d" % c["non_categorised"])
        self.stdout.write("General = %d" % c["gen_categorised"])