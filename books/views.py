from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .choices import language_choices, a_z
from django.contrib import messages
from taggit.models import Tag
from django.db.models import Count, Q, Min
from django.db.models.functions import Random
from authors.models import Author
from .models import Book, BookInstance2, Review, Category, BookTags, Series, BookInterest, BookTag
from .forms import SearchForm
from datetime import datetime, timedelta
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.urls import reverse_lazy
from PIL import Image
import re
from .collections import COLLECTIONS
from .search import normalise_query, build_search_filter, score_book, is_confident_redirect
from django.core.mail import send_mail

def get_related_collections(book):
    book_tag_names = set(book.book_tags.values_list("name", flat=True))
    related = []

    for slug, coll in COLLECTIONS.items():
        matches = book_tag_names.intersection(set(coll["tags"]))
        if len(matches) >= coll.get("min_match", 1):
            related.append({
                "slug": slug,
                "title": coll["title"],
                "description": coll["description"],
                "match_count": len(matches)
            })
    return sorted(related, key=lambda c: -c["match_count"])

def build_book_level_details(book):
    items = []

    if book.category:
        items.append(("Category", book.category.name))
    if book.language:
        items.append(("Language", book.language))
    if book.year:
        items.append(("Publication year", str(book.year)))
    
    return items

def build_copy_details(copy):
    items = []

    if copy.pages:
        items.append(("Pages", str(copy.pages)))
    if copy.book_type:
        items.append(("Format", copy.get_book_type_display()))
    if copy.publisher:
        items.append(("Publisher", copy.publisher))
    
    if copy.isbn13:
        items.append(("ISBN-13", copy.get_formatted_isbn13()))
    elif copy.isbn10:
        items.append(("ISBN-10", copy.get_formatted_isbn10()))
    
    return items

def build_details_block(book, copies_qs):
    copies = list(copies_qs)

    if len(copies) == 0:
        return {
            "heading": "No copies available",
            "mode": "none",
            "lists": [build_book_level_details(book)],
        }
    
    if len(copies) == 1:
        return {
            "heading": "1 copy available",
            "mode": "single",
            "lists": [build_copy_details(copies[0])],
        }
    
    return {
        "heading": f"{len(copies)} copies available",
        "mode": "multiple",
        "lists": [build_copy_details(c) for c in copies],
    }

def format_author_name(author_name):
    """
    Formats an author's name.
    For names like 'J.K. Rowling' or 'J R R Tolkien', combines initials into the first name.
    For regular names like 'John Adam George Smith', processes first, middle, and last names conventionally.
    """
    # Remove periods and normalize whitespace
    author_name = re.sub(r'\.', ' ', author_name).strip()
    names = author_name.split()
    
    if len(names) < 2:
        raise ValueError("Need to enter a first and last name for the author.")

    # Case 1: Initials-based names (e.g., "J R R Tolkien" -> "JRR Tolkien")
    if all(len(name) == 1 for name in names[:-1]):  # Check if all but the last are single characters
        first_name = ''.join(n.upper() for n in names[:-1])  # Combine all initials into the first name
        middle_name = ''  # No middle name for initials-based names
        if '-' in names[-1]:
            partials = names[-1].split('-')
            last_name = '-'.join(p.capitalize() for p in partials)
        else:
            last_name = names[-1].capitalize()
    else:
        # Case 2: Regular names (e.g., "John Adam George Alexander Smith")
        first_name = names[0].capitalize()
        middle_name = ' '.join(names[1:-1]).title() if len(names) > 2 else ''
        if '-' in names[-1]:
            partials = names[-1].split('-')
            last_name = '-'.join(p.capitalize() for p in partials)
        else:
            last_name = names[-1].capitalize()

    return first_name, middle_name, last_name

def is_valid_image(file):
    try:
        image = Image.open(file)
        image.verify()
        return True
    except Exception:
        return False

def index(request):
    categories = Category.objects.all()
    form = SearchForm()

    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'books/books.html', context)

def autocomplete_books(request):
    MAX_NUM_RESULTS = 5

    raw = request.GET.get('term', '')[:80].strip()
    terms = normalise_query(raw)

    if len(terms) == 0:
        return JsonResponse([], safe=False)

    q = build_search_filter(terms, allow_prefix=True)

    books_qs = (
        Book.objects
        .filter(q, instances__isnull=False)
        .distinct()[:20]
    )

    scored = []
    for book in books_qs:
        score = score_book(book, terms)
        scored.append((score, book))
    
    scored.sort(key=lambda item: (-item[0], item[1].title.lower()))

    results = []

    for score, book in scored[:MAX_NUM_RESULTS]:
        results.append({
            'label': book.title,
            'url': book.get_absolute_url(),
        })
    
    return JsonResponse(results, safe=False)

from reservations.models import Reservation
from staff.forms import AddBookCopy
# DELETE
def book_legacy(request, book_id, slug):
    book = get_object_or_404(Book, pk=book_id)

    try:
        copies = BookInstance2.objects.filter(book=book)
    except:
        copies = None
    try:
        available_copies = copies.filter(status='a')
    except:
        available_copies = None

    # other books in series
    other_books_in_series = None
    if book.series:
        other_books_in_series = Book.objects.filter(series=book.series).exclude(id=book.id).order_by('series_num')

    # similar books
    # ~~~~ changed 'tags' to 'book_tags'
    similar_books_initial = book.book_tags.similar_objects()

    # exclude other books in series from similar books
    if other_books_in_series:
        for other_book in other_books_in_series:
            if other_book in similar_books_initial:
                similar_books_initial.remove(other_book)

    # build new list only including same category
    similar_books = []
    if similar_books_initial:
        for bk in similar_books_initial:
            if bk.category == book.category:
                similar_books.append(bk)
            if len(similar_books) == 12:
                break
    del similar_books_initial

    # redundant code, but doing no harm really
    similar_books = similar_books[:12]

    # review stuff
    reviews = Review.objects.filter(book=book)
    has_not_reviewed = True
    if request.user.is_authenticated:
        if reviews.filter(user=request.user):
            has_not_reviewed = False

    copy_form = AddBookCopy()

    # determine if book was created with last week, for basic staff
    is_recently_created = book.created >= timezone.now() - timedelta(weeks=4)

    context = {
        'book': book,
        'copies': copies,
        'available_copies': available_copies,
        'reviews': reviews,
        'has_not_reviewed': has_not_reviewed,
        'other_books_in_series': other_books_in_series,
        'similar_books': similar_books,
        'copy_form': copy_form,
        'is_recently_created': is_recently_created,
    }

    return render(request, 'books/book.html', context)

def filter_by_tags(request):
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # changed 'books_taggedbook_items' to 'book_tags' - 
    # which i think is because of the related name used
    tags = Book.book_tags.all()
    dropdown_tags = tags.order_by('name')
    tags_popular = tags.annotate(
        num_times=Count('book_tags')).order_by('-num_times')[:20]
    context = {
        'tags': tags,
        'tags_popular': tags_popular,
        'dropdown_tags': dropdown_tags,
    }

    return render(request, 'books/tags.html', context)


def tag_search(request):
    queryset_list = Book.objects.all()
    selected_tags = []
    tag_strings = []
    search_path = 'tag_search?'

    if 'tag' in request.GET:
        tag_strings = request.GET.getlist('tag')

        #
        # NOTE: I thought about redirecting to the books by tag view
        # BUT figured it's better if people can search by multiple tags
        #
        # # a check to see if only one tag has been selected
        # if len(tag_strings) == 1:
        #     tag = get_object_or_404(Tag, name=tag_strings[0])
        #     return redirect('books_by_tag', tag.slug)

        for tag_string in tag_strings:
            search_path = search_path + 'tag=' + tag_string + '&'
            tag = get_object_or_404(BookTags, name=tag_string)
            selected_tags.append(tag)
            queryset_list = queryset_list.filter(book_tags__in=[tag])

    # language
    if 'language' in request.GET:
        language = request.GET['language']
        search_path = search_path + 'language=' + language
        if language != 'any':
            queryset_list = queryset_list.filter(language__icontains=language)


    num_results = queryset_list.count()

    paginator = Paginator(queryset_list, 30)
    page = request.GET.get('page')
    paged_books = paginator.get_page(page)

    tags = Book.book_tags.order_by('name')

    context = {
        'tags': tags,
        'selected_tags': selected_tags,
        'tag_strings': tag_strings,
        'tags': tags,
        'num_results': num_results,
        'language_choices': language_choices,
        'books': paged_books,
        'values': request.GET, # this is for getting the search terms to show up in the search results page
        'search_path': search_path,
    }
    return render(request, 'books/tag_search.html', context)

from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class BookUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    fields = ['title', 'category', 'summary', 'photo', 'year', 'is_featured']

    def test_func(self):
        # check if user is superuser
        if self.request.user.is_superuser:
            return True
        # check if user is staff and book was created within one week
        if self.request.user.is_staff and self.get_object().created >= timezone.now() - timedelta(weeks=4):
            return True
        # old check to see if user was just superuser
        # return self.request.user.is_superuser

class BookUpdateSuper(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    fields = '__all__'

    def test_func(self):
        return self.request.user.is_superuser

# I don't think this one is doing anything
class BookCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'other_authors', 'summary', \
        'book_tags', 'language', 'publish_date', 'photo', \
        'is_featured', 'series', 'series_num', 'category',
        ]
    initial = {'language': 'English',
               'is_featured': False,}

    def test_func(self):
        return self.request.user.is_staff

# To edit an instance. However, functionality already exists to delete/add instances, so fairly redundant. Still leaving it in
class BookInstanceUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BookInstance2
    fields = ['book_type', 'isbn13', 'isbn10', 'pages', 'publisher']

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        if self.request.user.is_staff and self.get_object().created >= timezone.now() - timedelta(weeks=4):
            return True
    def get_success_url(self):
        return reverse_lazy('book', kwargs={'book_id': self.object.book.id, 'slug': self.object.book.slug})

from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import FileSystemStorage

def format_book_title(title):
    # Define minor words to leave in lowercase (except the first word)
    minor_words = {'the', 'of', 'with', 'from', 'a', 'an', 'on', 'at', 'for', 'and', 'but', 'in', 'to', 'by', 'or', 'nor', 'as', 'so', 'yet', 'is'}

    words = title.split()

    # Capitalise first word
    # words[0] = words[0].capitalize()

    # Capitalize non-minor words and lowercase minor words
    for i in range(0, len(words)):
        word = words[i]

        # Skip words starting with a number
        if word[0].isdigit():
            continue

        # Skip words that are entirely uppercase
        if word.isupper():
            continue

        # Deal with hyphenated word
        if '-' in word:
            parts = word.split('-')
            words[i] = '-'.join(part.capitalize() for part in parts)
            continue

        # Deal with French d' elision
        if word.lower().startswith("d'"):
            words[i] = f"d'{word[2:].capitalize()}"
            continue

        # Deal with words starting with 'Mc' (could also do 'Mac'?)
        if word.lower().startswith('mc') and len(word) > 2:
            words[i] = f"Mc{word[2:].capitalize()}"
            continue

        # Capitalise the first word of a title regardless
        if i == 0:
            words[0] = word.capitalize()
            continue

        # Capitalise non-minor words and lowercase minor words
        if word.lower() in minor_words:
            words[i] = word.lower()
        else:
            words[i] = word.capitalize()

    # Rejoin the words into a single string
    formatted_title = ' '.join(words)

    def capitalize_after_symbols(title):
        # List of symbols to check for
        symbols = [': ', '& ', '/ ']
        for symbol in symbols:
            if symbol in title:
                initial, rest = title.split(symbol, 1)
                if rest and rest[0].isalpha():
                    # Rebuild the title with character after symbol capitalised
                    title = f"{initial}{symbol}{rest[0].upper()}{rest[1:]}"
        return title
    
    formatted_title = capitalize_after_symbols(formatted_title)

    # Handle titles with a colon
    # if ': ' in formatted_title:
        # initial, rest = formatted_title.split(': ', 1)
        # if rest and rest[0].isalpha():
        #     formatted_title = f"{initial}: {rest[0].upper()}{rest[1:]}"

    # Move starting 'The', 'A', or 'An' to the end
    if formatted_title.lower().startswith(('the ', 'a ', 'an ')):
        first_word, rest_of_title = formatted_title.split(' ', 1)
        formatted_title = f"{rest_of_title}, {first_word}"

    return formatted_title

@staff_member_required
def process_author(request, title):
    """
    Processes the author based on the form input.
    Returns an Author object or raises a validation error with appropriate messages.
    """
    if 'author_select' in request.POST and request.POST['author_select'].strip():
        # Author selected from the dropwdown
        author_id = int(request.POST.get('author_select'))
        author = get_object_or_404(Author, id=author_id)

        # Check if the book already exists for the selected author
        if Book.objects.filter(title__iexact=title, author=author).exists():
            raise ValueError('Book already in database')
        
        return author
    
    elif request.POST['author'].strip():
        # Author entered manually
        try:
            first_name, middle_name, last_name = format_author_name(request.POST['author'].strip())
            author = Author.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name
            ).first()

            # Check if the book already exists for the entered author
            if author and Book.objects.filter(title__iexact=title, author=author).exists():
                raise ValueError('Book already in database')
            
            # Create a tentative author object if not found in the database
            if not author:
                author = Author(first_name=first_name, middle_names=middle_name, last_name=last_name)

            return author
        except ValueError as e:
            raise ValueError(str(e))
    
    else:
        # No author selected or entered
        raise ValueError('Please select or enter an author')


@staff_member_required
def add_book(request):
    # Common context data for the form
    def get_context(form_data=None):
        book_types = {
            'p': 'Paperback',
            'h': 'Hardcover',
            'o': 'Oversized',
        }
        authors = Author.objects.all()
        categories = Category.objects.all()
        series = Series.objects.all()
        # tags = BookTags.objects.all()
        main_tags = BookTags.objects.filter(band=1)

        selected_tags = []
        if form_data and 'main_tags' in form_data:
            selected_tags = form_data.getlist('main_tags')

        return {
            'authors': authors,
            'categories': categories,
            'series': series,
            # 'tags': tags,
            'book_types': book_types,
            'main_tags': main_tags,
            'form_data': form_data,
            'selected_tags': selected_tags
        }

    if request.method == 'POST':
        # print(request.POST)
        # Get and format the title
        title = request.POST.get('title', '').strip()

        if not title:
            messages.error(request, 'Empty spaces for titles are not accepted')
            return render(request, 'books/add_book.html', get_context(request.POST))
        
        title = format_book_title(title)

        # Get an author object using request
        try:
            author = process_author(request, title)
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'books/add_book.html', get_context(request.POST))
        
        # Collect the other form inputs

        category = get_object_or_404(Category, id=int(request.POST['category']))
        book_type = request.POST['book_type']

        series = None
        if request.POST['series_select'] != 'ignore':
            series = get_object_or_404(Series, id=int(request.POST['series_select']))
        elif request.POST['series']:
            name = request.POST['series']
            try:
                series = Series.objects.get(name=name)
            except Series.DoesNotExist:
                series = Series(name=name)
                # haven't saved series yet

        series_num = None
        if request.POST['series_num']:
            num = int(request.POST['series_num'])
            if num > 0:
                series_num = num

        if series and not series_num:
            series_num = 99

        summary = ''
        if request.POST['summary']:
            summary = request.POST['summary']
            if len(summary) > 2000:
                summary = summary[:1997] + '...'

        # Deal with the image input
        photo = None
        max_size_mb = 1

        if request.FILES.get('photo', False):
            photo = request.FILES['photo']

            # Check file size
            if photo.size > max_size_mb * 1024 * 1024:
                messages.error(request, f"Image file size exceeds the maximum limit of {max_size_mb}MB.")
                return render(request, 'books/add_book.html', get_context(request.POST))
            
            # Add a .jpg extension to the file if it doesn't have one
            if '.' not in photo.name:
                photo.name += '.jpg'

            # Check the file is an image
            if not is_valid_image(photo):
                messages.error(request, "The uploaded file is not a valid image.")
                return render(request, 'books/add_book.html', get_context(request.POST))


        isbn13 = None
        if request.POST['isbn13']:
            isbn13 = request.POST['isbn13']

        isbn10 = None
        if request.POST['isbn10']:
            isbn10 = request.POST['isbn10']

        pages = None
        if request.POST['pages']:
            pages = int(request.POST['pages'])
            if pages < 1:
                pages = None

        publisher = ''
        if request.POST['publisher']:
            publisher = request.POST['publisher']

        # I'm disabling adding in a full publication date cos of Val (2/11/21)
        #publish_date = None
        #if request.POST['publish_date']:
        #    publish_date = datetime.strptime(request.POST['publish_date'], "%d/%m/%Y").date()

        year = None
        if request.POST['year']:
            year = request.POST['year']

        # I've disabled book tags
        # book_tags = None
        # if request.POST['book_tags']:
        #     book_tags = [x.strip().lower() for x in request.POST['book_tags'].split(',')]

        is_featured = 'is_featured' in request.POST

        # now the adding stuff
        author.save()
        if series:
            series.save()

        book = Book.objects.create(
            title=title,
            author=author,
            other_authors='',
            summary=summary,
            series=series,
            series_num=series_num,
            category=category,
            photo=photo,
            year=year,
            #publish_date=publish_date,
            is_featured=is_featured,
        )

        # I've disabled book_tags
        # if book_tags:
        #     for tag in book_tags:
        #         book.book_tags.add(tag)
        #     book.save()

        if 'main_tags' in request.POST:
            tag_names = request.POST.getlist('main_tags')
            for tag_name in tag_names:
                book.book_tags.add(tag_name)
            book.save()

        copies = 1
        if request.POST['copies']:
            copies = int(request.POST['copies'])
            if not (copies > 0) and (copies < 6):
                copies = 1

        for i in range(copies):
            instance = BookInstance2.objects.create(
                book=book,
                pages=pages,
                isbn10=isbn10,
                isbn13=isbn13,
                publisher=publisher,
                book_type=book_type,
            )

        messages.success(request, 'Book has been successfully added')
        return redirect(book)
            
    else: # GET request
        return render(request, 'books/add_book.html', get_context())


# trying to test out a share book email thing
# from .forms import EmailPostForm
# def book_share(request, book_id):
#   # retrieve book by id
#   book = get_object_or_404('Book', id=book_id)
#   if request.method == 'POST':
#       # form was submitted
#       form = EmailPostForm(request.POST)
#       if form.is_valid():
#           # form fields passed validation
#           cd = form.cleaned_data
#           # send email
#   else:
#       form = EmailPostForm()

#   context = {
#       'post': post,
#       'form': form,
#   }
#   return render(request, 'books/share.html', context)

from django.contrib.auth.decorators import login_required

@login_required
def add_review(request, book_id, body=None):
    book = Book.objects.get(id=book_id)
    if request.method == 'POST':

        # perform checks
        if request.POST.get('body'):
            body = request.POST.get('body')

            if request.POST.get('title'):
                title = request.POST.get('title')

                # rating - note, don't need to check if there is one,
                # cos default is set to None (0) so there will
                # always be a rating
                rating = int(request.POST.get('rating'))
                if rating == 0:
                    rating = None

                # add review
                user = request.user
                review = Review(
                    book=book,
                    user=user,
                    title=title,
                    body=body,
                    rating=rating,
                    )
                review.save()

                messages.success(request, 'Your review has been posted')
                return redirect(book)

            else:
                messages.error(request, 'You have not entered in a title')
                return redirect('add_review', book, body)

        else:
            messages.error(request, 'You have not entered in a review')
            return redirect('add_review', book)

    else:
        rating_choices = {
            '1':'Poor',
            '2':'Average',
            '3':'Good',
            '4':'Very Good',
            '5':'Excellent',
        }
        context = {
            'book': book,
            'rating_choices': rating_choices,
        }
        return render(request, 'books/add_review.html', context)

from django.http import HttpResponse

def books_filtered(request, letter_choice=None, tag_slug=None):

    #books = Book.objects.all()
    # taken above line out 2/11/21 and replaced it with following
    # which only includes books that have instances
    books = Book.objects.filter(instances__isnull=False).distinct()

    tag = None
    letter = None

    # two ways of filtering - tag or letter
    if tag_slug:
        #~~~~~~~~~~~~
        # changed 'Tag' to 'BookTags'
        tag = get_object_or_404(BookTags, slug=tag_slug)
        #~~~~~~~~~~~~
        # changed 'tags__in' to 'book_tags__in'
        books = books.filter(book_tags__in=[tag])
    else:
        if letter_choice:
            if letter_choice == '0':
                letter = '0-9'
                books=books.filter(title__regex=r'^\d')
            else:
                letter = letter_choice
                books = books.filter(title__istartswith=letter)
        else:
            letter = 'a'
            books = books.filter(title__istartswith=letter)

    # to show number of results
    num_results = books.count()

    paginator = Paginator(books, 24)
    page_number = request.GET.get('page')
    paged_books = paginator.get_page(page_number)
    
    #~~~~~~~~~~~~
    # changed 'tags' to 'book_tags'
    all_tags = Book.book_tags.all()

    context = {
        'tag': tag,
        'all_tags': all_tags,
        'letter': letter,
        'books': paged_books,
        'alphabet': a_z,
        'num_results': num_results,
    }

    return render(request,
                  'books/books_filtered.html',
                  context)

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

def book_search(request):
    form = SearchForm()
    query = None
    category = None
    results = []
    tags = Book.book_tags.all()
    categories = Category.objects.all() 

    # the initial part instantiates the form with either the
    # query from navbar search or query from regular search
    #### new search technique ####
    if ('navbar_query' in request.GET) or ('keywords' in request.GET): # or ('query' in request.GET)
        if 'navbar_query' in request.GET:
            # for some weird reason needed to set up a dict
            form = SearchForm({'query': request.GET['navbar_query']})
        elif 'keywords' in request.GET:
            form = SearchForm({'query': request.GET['keywords']})
        # elif 'query' in request.GET:
        #     form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + \
                            SearchVector('author__last_name', weight='A') + \
                            SearchVector('author__first_name', weight='B')
            search_query = SearchQuery(query)
            
            # Rank search results using Postgres search
            results = Book.objects.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(rank__gte=0.3).order_by('-rank').distinct()

            # For non-staff users, only show books with instances
            if not request.user.is_staff:
                results = results.filter(instances__isnull=False)

            if 'category' in request.GET:
                category_id = int(request.GET['category'])
                if category_id != -1:
                    category = get_object_or_404(Category, pk=category_id)
                    results = results.filter(category=category)

            tags = tags.filter(name__icontains=query)

    context = {
        'form': form,
        'query': query,
        'results': results,
        'tags': tags,
        'category': category,
        'categories': categories,
    }
    return render(request, 'books/book_search.html', context)

from django.views.decorators.http import require_POST

@login_required
@require_POST
def book_like(request):
    book_id = request.POST.get('id')
    action = request.POST.get('action')

    if not book_id or action not in ('like', 'unlike'):
        return JsonResponse({'status': 'error'})
    
    book = get_object_or_404(Book, id=book_id)

    if action == 'like':
        book.users_like.add(request.user)
    else:
        book.users_like.remove(request.user)
    
    return JsonResponse({
        'status': 'ok',
        'likes': book.users_like.count(),
    })

@login_required
def del_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if request.user == review.user:
        title = review.book.title
        review.delete()
        messages.success(request, 'Your review for ' + title + ' has been deleted')
        return redirect('dashboard')
    else:
        messages.error(request, 'You cannot delete a review you did not write')
        return redirect('books')

def category(request, category_code):
    categories = Category.objects.all()
    category = get_object_or_404(Category, code=category_code)
    category_books = Book.objects.filter(category=category)
    featured_books = category_books.filter(is_featured=True)

    if len(featured_books)%4==0:
        num_slides = int(len(featured_books)/4)
    else:
        num_slides = int(len(featured_books)//4) + 1
    
    num_slides_string = ''
    for i in range(num_slides):
        num_slides_string = num_slides_string + str(i)

    # what a tremendous piece of code
    popular_authors = Author.objects.annotate(
        num_times=Count('books', filter=Q(books__in=category_books))).order_by('-num_times')[:10]

    series_with_multiple_books = Series.objects.annotate(
        num_times=Count('books', filter=Q(books__in=category_books))).order_by('-num_times')[:10]

    context = {
        'category': category,
        'categories': categories,
        'category_books': category_books,
        'featured_books': featured_books,
        'popular_authors': popular_authors,
        'series_with_multiple_books': series_with_multiple_books,
        'num_slides_string': num_slides_string,
    }
    return render(request, 'books/category.html', context)

from .models import BookForSale, SaleCategory

def books_for_sale_list(request, sale_category_code=None):
    sale_category = None
    # books = BookForSale.objects.filter(is_sold=False)
    # books = BookForSale.objects.all()
    books = BookForSale.objects.order_by('is_sold', 'title')
    categories = SaleCategory.objects.all()

    # Filter by category if provided
    if sale_category_code:
        sale_category = get_object_or_404(SaleCategory, code=sale_category_code)
        books = books.filter(sale_category=sale_category)

    # Search functionality
    query = request.GET.get('q', '')
    if query:
        # Split the query into terms (e.g., "delia cook" -> ['delia', 'cook'])
        query_terms = query.split()

        # Create a base Q object
        search_conditions = Q()

        # Loop through each term and search across title, first_name, middle_names, and last_name
        for term in query_terms:
            search_conditions |= Q(title__icontains=term)  # Search in book title
            search_conditions |= Q(author__first_name__icontains=term)  # Search in author's first name
            search_conditions |= Q(author__last_name__icontains=term)  # Search in author's last name

        # Apply the search conditions to the books queryset
        books = books.filter(search_conditions)

    # Paginate the results (12 per page)
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'sale_category': sale_category,
        'books': page_obj,
        'categories': categories,
        'query': query,
    }

    return render(request, 'books/books_for_sale_list.html', context)

def book_for_sale_detail(request, slug):
    book = get_object_or_404(BookForSale, slug=slug)
    return render(request, 'books/book_for_sale_detail.html', {'book': book})

from .forms import BookForSaleForm
# View for creating a book for sale
class BookForSaleCreateView(UserPassesTestMixin, CreateView):
    model = BookForSale
    form_class = BookForSaleForm
    template_name = 'books/book_for_sale_form.html'

    def form_valid(self, form):
        new_author_name = form.cleaned_data.get('new_author')
        if new_author_name:
            names = new_author_name.strip().split()

            # Ensure there are at least 2 names
            if len(names) < 2:
                form.add_error('new_author', 'Please enter at least a first name and a last name.')
                return self.form_invalid(form)
            
            first_name = names[0].capitalize()
            last_name = names[-1].capitalize()

            middle_names = ' '.join(name.capitalize() for name in names[1:-1])

            # Create or retrieve the author
            author, created = Author.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={'middle_names': middle_names}
            )

            # Associate the author with the form instance
            form.instance.author = author
        
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('book_for_sale_detail', kwargs={'slug': self.object.slug})
    
# View for editing book for sale
class BookForSaleUpdateView(UserPassesTestMixin, UpdateView):
    model = BookForSale
    form_class = BookForSaleForm
    template_name = 'books/book_for_sale_form.html'

    def form_valid(self, form):
        new_author_name = form.cleaned_data.get('new_author')
        if new_author_name:
            names = new_author_name.strip().split()

            # Ensure there are at least 2 names
            if len(names) < 2:
                form.add_error('new_author', 'Please enter at least a first name and a last name.')
                return self.form_invalid(form)
            
            first_name = names[0].capitalize()
            last_name = names[-1].capitalize()

            middle_names = ' '.join(name.capitalize() for name in names[1:-1])

            # Create or retrieve the author
            author, created = Author.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={'middle_names': middle_names}
            )

            # Associate the author with the form instance
            form.instance.author = author
        
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('book_for_sale_detail', kwargs={'slug': self.object.slug})


import requests
import os
from django.conf import settings

# def fetch_book_cover(isbn):
#     """
#     Fetches the cover image for a book using its ISBN from the Open Library API.

#     Args:
#         isbn (str): The ISBN of the book.

#     Returns:
#         bytes: The binary content of the book cover image if found, None otherwise.
#     """
#     url = f'https://openlibrary.org/search.json?isbn={isbn}'

#     try:
#         print(f'Fetching book cover for ISBN: {isbn}')
#         response = requests.get(url)
#         response.raise_for_status()
#         data = response.json()

#         book_info = data.get('docs', [])
#         if book_info:
#             first_book = book_info[0]
#             cover_edition_key = first_book.get('cover_edition_key')
#             cover_i = first_book.get('cover_i')

#             image_url = None
#             if cover_edition_key:
#                 image_url = f'https://covers.openlibrary.org/b/olid/{cover_edition_key}-L.jpg'
#             elif cover_i:
#                 image_url = f'https://covers.openlibrary.org/b/id/{cover_i}-L.jpg'
            
#             if image_url:
#                 print(f"Downloading image from URL: {image_url}")
#                 response = requests.get(image_url, stream=True)
#                 response.raise_for_status()
#                 print(f'Size of image is: {len(response.content)}')
#                 return response.content
#             else:
#                 print("No image URL found.")
#                 return None
#         else:
#             print("No book information found.")
#             return None
#     except Exception as e:
#         print(f"Error fetching book data: {e}")
#         return None

def fetch_book_cover(isbn, size='L'):
    """
    Fetches the cover image for a book using its ISBN from the Open Library Covers API.

    Args:
        isbn (str): The ISBN of the book.
        size (str): One of 'S', 'M', 'L'

    Returns:
        bytes | None: Image content if found, otherwise None.
    """
    url = f'https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg'

    try:
        print(f'Fetching cover from: {url}?default=false')
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            print(f'No cover found for ISBN.')
            return None

        response.raise_for_status()
        return response.content
    
    except requests.RequestException as e:
        print(f'Error fetching cover image: {e}')
        return None

@staff_member_required
def lookup_book_for_sale_cover(request, book_id):
    """
    Looks up and displays a temporary cover image for a BookForSale based on its ISBN.
    """

    # Get the BookForSale object
    book_for_sale = get_object_or_404(BookForSale, id=book_id)

    # Check if the book already has a cover image
    if book_for_sale.photo:
        messages.error(request, 'This book already has a cover image.')
        return redirect(book_for_sale.get_absolute_url())

    # Check if the book has an ISBN
    if not book_for_sale.isbn:
        messages.warning(request, 'This book does not have an ISBN. Please add one.')
        return redirect(book_for_sale.get_absolute_url())

    # Fetch book cover using the ISBN
    image_content = fetch_book_cover(book_for_sale.isbn)

    if image_content is None:
        messages.warning(request, 'No cover image found on Open Library for this ISBN.')
        return redirect(book_for_sale.get_absolute_url())

    # Check the image size
    image_size = len(image_content)
    max_image_size = 1024 * 1024  # 1MB
    if image_size > max_image_size:
        messages.error(request, 'Image exceeds the maximum allowed size of 1MB.')
        return redirect(book_for_sale.get_absolute_url())

    # Save the image temporarily
    temp_folder = os.path.join(settings.MEDIA_ROOT, 'temp')
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    temp_image_path = os.path.join(temp_folder, 'cover_image.jpg')
    with open(temp_image_path, 'wb') as temp_image_file:
        temp_image_file.write(image_content)

    # Get the temporary image URL
    temp_image_url = os.path.join(settings.MEDIA_URL, 'temp', 'cover_image.jpg')

    context = {
        'book': book_for_sale,
        'temp_image_url': temp_image_url
    }

    return render(request, 'books/lookup_book_cover.html', context)

@staff_member_required
def associate_book_for_sale_cover(request, book_id):
    """
    Associates the temporary book cover with the BookForSale object.
    """

    book_for_sale = get_object_or_404(BookForSale, id=book_id)

    if request.method == 'POST':
        temp_image_path = os.path.join(settings.MEDIA_ROOT, 'temp', 'cover_image.jpg')

        if os.path.exists(temp_image_path):
            # Associate the book cover image with the BookForSale model
            with open(temp_image_path, 'rb') as temp_image_file:
                book_for_sale.photo.save('cover_image.jpg', temp_image_file, save=True)

            # Remove the temporary image file
            os.remove(temp_image_path)

            messages.success(request, 'Image successfully associated with the book!')
            return redirect(book_for_sale.get_absolute_url())

        else:
            messages.error(request, 'Temporary image file not found!')
            return redirect(book_for_sale.get_absolute_url())

    return redirect(book_for_sale.get_absolute_url())

@staff_member_required
def delete_book_for_sale(request, slug):
    book = get_object_or_404(BookForSale, slug=slug)
    author = book.author

    if request.method == 'POST':
        book.delete()
        messages.success(request, f'The book "{book.title}" was successfully deleted.')

        has_other_books = Book.objects.filter(author=author).exists()
        has_other_books_for_sale = BookForSale.objects.filter(author=author).exists()

        if not has_other_books and not has_other_books_for_sale:
            author.delete()
            messages.info(request, f'Author "{author}" was also deleted because they have no other books.')

        return redirect('books_for_sale_list')




def collections_index(request):
    context = {
        'collections': COLLECTIONS
    }
    return render(request, 'books/collections.html', context)

from urllib.parse import urlencode

def collection_detail(request, slug):
    try:
        collection = COLLECTIONS[slug]
    except KeyError:
        raise Http404('Collection not found')

    MIN_MATCH = collection.get('min_match', 1)

    tags = BookTags.objects.filter(name__in=collection['tags'])

    books_qs = (
        Book.objects
        .filter(book_tags__in=tags)
        .annotate(
            matched_tags=Count(
                'book_tags',
                filter=Q(book_tags__in=tags),
                distinct=True
            )
        )
        .filter(matched_tags__gte=MIN_MATCH)
    )

    sort = request.GET.get('sort', 'relevance')

    if sort == 'title':
        books_qs = books_qs.order_by('title')
    elif sort == 'newest':
        books_qs = books_qs.order_by('-created')
    else:
        books_qs = books_qs.order_by('-matched_tags', 'title')

    paginator = Paginator(books_qs, 30)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    total_books = books_qs.count()

    base_params = {}
    if (sort and sort != 'relevance'):
        base_params['sort'] = sort

    context = {
        'collection': collection,
        'books': page_obj,
        'total_books': total_books,
        'sort': sort,
        'base_querystring': urlencode(base_params),
    }

    return render(request, 'books/collection_detail.html', context)



def explore_books(request):
    FEATURED_COUNT = 16
    NEW_COUNT = 16
    AUTHOR_COUNT = 5
    SERIES_COUNT = 6
    SHORT_READS_COUNT = 10

    featured_books = (
        Book.objects
        .filter(is_featured=True)
        .order_by('-updated', '-created')[1:FEATURED_COUNT]
    )

    new_books = (
        Book.objects
        .exclude(is_featured=True)
        .order_by('-created')[:NEW_COUNT]
    )

    popular_authors = (
        Author.objects
        .annotate(num_books=Count('books'))
        .filter(num_books__gte=2)
        .order_by('-num_books')[:AUTHOR_COUNT]
    )

    popular_series = (
        Series.objects
        .annotate(num_books=Count('books'))
        .filter(num_books__gte=3)
        .order_by('-num_books')[:SERIES_COUNT]
    )

    short_reads = (
        Book.objects
        .filter(instances__pages__isnull=False)
        .annotate(min_pages=Min('instances__pages'))
        .filter(min_pages__lte=200)
        .order_by('min_pages')[:SHORT_READS_COUNT]
    )

    featured_collections = {
        slug: data
        for slug, data in COLLECTIONS.items()
        if data.get("featured") is True
    }

    # recommended_books = (
    #     Book.objects
    #     .filter(is_featured=True)
    #     .order_by('?')[:2]
    # )

    recommended_books = (
        Book.objects
        .filter(slug__in=[
            "girl-on-the-train-the",
            "never-let-me-go",
        ])
    )

    rec_one, rec_two = list(recommended_books)

    
    context = {
        'featured_books': featured_books,
        'new_books': new_books,
        'popular_authors': popular_authors,
        'popular_series': popular_series,
        'short_reads': short_reads,
        'featured_collections': featured_collections,
        # 'recommended_books': recommended_books,
        'rec_one': rec_one,
        'rec_two': rec_two,
    }
    return render(request, 'books/explore.html', context)


def book_search_redux(request):
    raw = request.GET.get('q', '')[:80].strip()
    terms = normalise_query(raw)
    if not terms:
        return redirect('explore_books')

    q = build_search_filter(terms)

    books_qs = Book.objects.filter(q)

    if not request.user.is_staff:
        books_qs = books_qs.filter(instances__isnull=False)
    
    books_list = list(books_qs.distinct())
    scored_books = []
    for book in books_list:
        book_score = score_book(book, terms)
        scored_books.append((book_score, book))
    
    scored_books.sort(
        key=lambda item: (-item[0], item[1].title.lower())
    )

    if len(scored_books) == 1:
        book = scored_books[0][1]
        if is_confident_redirect(book, terms):
            return redirect(book.get_absolute_url())

    results = [item[1] for item in scored_books]
    
    paginator = Paginator(results, 30)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    total_books = len(results)
    base_params = { 'q': raw }

    context = {
        'query': raw,
        'books': page_obj,
        'total_books': total_books,
        'base_querystring': urlencode(base_params),
    }

    return render(request, 'books/search_results.html', context)



import random
def book(request, book_id, slug):
    # =========================
    # BOOK SELECTION STRATEGY
    # =========================

    # USE_RANDOM_BOOK = True
    # FIXED_BOOK_ID = 1071 #1791 #1178

    # if USE_RANDOM_BOOK:
    #     ids = Book.objects.values_list("id", flat=True)
    #     book_id = random.choice(list(ids))
    #     book = get_object_or_404(Book, pk=book_id)
    # else:
    #     book = get_object_or_404(Book, pk=FIXED_BOOK_ID)
    book = get_object_or_404(Book, pk=book_id)

    # -------------------
    # Author count
    # -------------------
    author_extra_books_count = (
        book.author
            .books
            .exclude(id=book.id)
            .count()
    )
    # -------------------
    # Book interest
    # -------------------
    interest = None
    if request.user.is_authenticated:
        interest = BookInterest.objects.filter(book=book, user=request.user).first()

    # -------------------
    # Copies & details
    # -------------------
    copies = book.instances.all()
    num_copies = copies.count()
    details_block = build_details_block(book, copies)

    # -------------------
    # Related collections
    # -------------------
    related_collections = get_related_collections(book)

    # -------------------
    # Series books
    # -------------------
    other_books_in_series = []
    if book.series:
        other_books_in_series = (
            Book.objects
                .filter(series=book.series)
                .exclude(id=book.id)
                .order_by('series_num')
        )

    # -------------------
    # Similar books
    # -------------------
    similar_books = []
    MAX_LENGTH_SIMILAR_BOOKS = 12

    initial_similar_books = book.book_tags.similar_objects()

    # Remove books that are already in the same series
    if other_books_in_series:
        series_book_ids = set(b.id for b in other_books_in_series)
    else:
        series_book_ids = set()

    for candidate in initial_similar_books:

        # Skip if it's in the same series
        if candidate.id in series_book_ids:
            continue
        
        # Skip if it's not the same category
        if candidate.category_id != book.category_id:
            continue

        similar_books.append(candidate)

        if len(similar_books) == MAX_LENGTH_SIMILAR_BOOKS:
            break

    # -------------------
    # Reviews
    # -------------------
    reviews = Review.objects.filter(book=book, active=True)
    has_not_reviewed = True
    if request.user.is_authenticated:
        if reviews.filter(user=request.user):
            has_not_reviewed = False
    review_nums = [1, 2, 3, 4, 5]

    has_not_reviewed = True
    if request.user.is_authenticated:
        has_not_reviewed = not reviews.filter(user=request.user).exists()

    # -------------------
    # Staff related
    # -------------------
    is_recently_created = book.created >= timezone.now() - timedelta(weeks=4)

    copy_form = AddBookCopy()

    context = {
        'copy_form': copy_form,
        'book': book,
        'interest': interest,
        'author_extra_books_count': author_extra_books_count,
        'related_collections': related_collections,
        'details_block': details_block,
        'num_copies': num_copies,
        'other_books_in_series': other_books_in_series,
        'similar_books': similar_books,
        'reviews': reviews,
        'has_not_reviewed': has_not_reviewed,
        'review_nums': review_nums,
        'is_recently_created': is_recently_created,
    }

    return render(request, "books/book.html", context)

from django.conf import settings

@login_required
@require_POST
def register_interest(request):
    book = get_object_or_404(Book, id=request.POST.get('book_id'))

    interest, created = BookInterest.objects.get_or_create(
        book=book,
        user=request.user,
    )

    if created:
        send_mail(
            f'Book interest: {book.title}',
            f'{request.user.username} is interested in "{book.title}.',
            settings.EMAIL_HOST_USER,
            ['sb1664@gmail.com'],
            fail_silently=True,
        )
    
    return JsonResponse({
        'status': 'ok',
        'created': created,
        'handled': interest.handled,
    })

@require_POST
@login_required
def delete_interest(request):
    book_id = request.POST.get('book_id')

    deleted, _ = BookInterest.objects.filter(
        book_id=book_id,
        user=request.user
    ).delete()

    return JsonResponse({
        'status': 'ok',
        'deleted': deleted
    })

@require_POST
@staff_member_required
def mark_interest_handled(request, pk):
    interest = get_object_or_404(BookInterest, pk=pk)
    interest.handled = True
    interest.save(update_fields=["handled"])

    messages.success(request, 'Interest marked as handled.')
    return redirect("staff_book_interests")

import string
A_Z = list(string.ascii_uppercase)
A_Z.append('0-9')

def books_a_z(request, letter='A'):
    letter = letter.upper()

    books = Book.objects.all()

    if letter == '0-9':
        books = books.filter(title__regex=r'^\d')
    else:
        books = books.filter(title__istartswith=letter)

    books = books.order_by('title')

    paginator = Paginator(books, 30)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    context = {
        'books': page_obj,
        'letter': letter,
        'alphabet': A_Z,
        'num_results': books.count(),
    }

    return render(request, 'books/books_a_z.html', context)

from .forms import ReviewForm

class ReviewBaseMixin(LoginRequiredMixin):
    model = Review
    form_class = ReviewForm

    def get_success_url(self):
        return self.object.book.get_absolute_url()
    
    def form_valid(self, form):
        messages.success(self.request, 'Your review has been saved.')
        return super().form_valid(form)

class ReviewCreateView(ReviewBaseMixin, CreateView):
    template_name = "books/review_form.html"

    def get_initial(self):
        initial = super().get_initial().copy()
        initial['title'] = "My Review of this Book"
        initial['rating'] = 5
        return initial

    def dispatch(self, request, *args, **kwargs):
        book = get_object_or_404(Book, pk=self.kwargs["book_id"])
        if Review.objects.filter(book=book, user=request.user).exists():
            messages.info(request, "You’ve already reviewed this book.")
            return redirect(book)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.book_id = self.kwargs["book_id"]
        form.instance.user = self.request.user
        return super().form_valid(form)


class ReviewUpdateView(ReviewBaseMixin, UserPassesTestMixin, UpdateView):
    template_name = "books/review_form.html"

    def test_func(self):
        return self.get_object().user == self.request.user

class ReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Review
    template_name = "books/review_confirm_delete.html"

    def test_func(self):
        return self.get_object().user == self.request.user

    def get_success_url(self):
        messages.success(self.request, "Your review was deleted.")
        return self.object.book.get_absolute_url()

from django.utils.decorators import method_decorator

@method_decorator(staff_member_required, name="dispatch")
class StaffBookInterestDeleteView(LoginRequiredMixin, DeleteView):
    model = BookInterest
    template_name = "books/interest_confirm_delete.html"
    success_url = reverse_lazy("staff_book_interests")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "The interest has been deleted.")
        return super().delete(request, *args, **kwargs)

    # def test_func(self):
    #     return self.request.user.is_staff

    # def get_success_url(self):
    #     messages.success(self.request, "The interest has been deleted.")
    #     return redirect("staff_book_interests")

@method_decorator(staff_member_required, name="dispatch")
class StaffBookInterestListView(ListView):
    model = BookInterest
    template_name = "books/staff_interest_list.html"
    context_object_name = "interests"
    paginate_by = 25

    def get_queryset(self):
        return (
            BookInterest.objects
            .select_related("user", "book")
            .order_by("handled", "-created")
        )

def series_detail(request, series_id):
    series = get_object_or_404(
        Series.objects.annotate(book_count=Count("books")),
        id=series_id
    )

    books = (
        Book.objects
        .filter(series=series)
        .order_by("series_num", "title")
    )

    authors = Author.objects.filter(books__series=series).distinct()
    tags = (
        BookTags.objects
        .filter(book_tags__content_object__series=series)
        .distinct()
        .order_by("band", "name")
    )

    return render(
        request,
        "books/series_detail.html",
        {
            "series": series,
            "books": books,
            "authors": authors,
            "tags": tags,
        }
    )