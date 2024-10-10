from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .choices import language_choices, a_z
from django.contrib import messages
from taggit.models import Tag
from django.db.models import Count
from authors.models import Author
from .models import Book, BookInstance2, Review, Category, BookTags, Series
from .forms import SearchForm
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse_lazy

def index(request):
    categories = Category.objects.all()
    form = SearchForm()

    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'books/books.html', context)

def autocomplete_books(request):
    if 'term' in request.GET:
        term = request.GET.get('term')

        # Handles articles ('the', 'a') to improve search results
        if term.startswith('the '):
            term = term[4:]
        if term.startswith('a '):
            term = term[2:]
        
        if term != 'the' and len(term) > 2:
            # Get books that match the search term
            books = Book.objects.filter(title__icontains=term, instances__isnull=False).distinct()[:10]

            results = []
            for book in books:
                results.append({
                    'label': book.title,
                    'url': book.get_absolute_url(),
                })

            return JsonResponse(results, safe=False)
        
        return JsonResponse([], safe=False) # Empty response if no term or no matches

from reservations.models import Reservation
from staff.forms import AddBookCopy
def book(request, book_id, slug):
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

from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class BookUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    fields = ['title', 'category', 'summary', 'photo', 'year']

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

@staff_member_required
def add_book(request):
    if request.method == 'POST':
        if 'title' in request.POST:
            title = request.POST['title']
            if title.startswith(('The ', 'the ')):
                title = title[4:] + ', The'
            elif title.startswith(('A ', 'a ')):
                title = title[2:] + ', A'
            # now we have a title in the correct format

            # if an author has been selected
            if 'author_select' in request.POST:
                author_id = int(request.POST.getlist('author_select')[0])
                author = get_object_or_404(Author, id=author_id)

                if Book.objects.filter(title__iexact=title, author=author):
                    messages.error(request, 'Book already in database')
                    return redirect('add_book')





            # if an author has been selected
            # if request.POST['author_select'] != 'ignore':
            #     author = get_object_or_404(Author, id=int(request.POST['author_select']))
            #     # now we have author

            #     if Book.objects.filter(title__iexact=title, author=author):
            #         messages.error(request, 'Book already in database')
            #         return redirect('add_book')

            # else if an author has been entered in
            elif request.POST['author']:
                names = request.POST['author'].strip().split()
                if len(names) == 1:
                    messages.error(request, 'Need to enter a first and last name for author')
                    return redirect('add_book')
                else:
                    first_name = names[0].capitalize()
                    del names[0]
                    last_name = names[-1].capitalize()
                    del names[-1]
                    middle_name = ''
                    if names:
                        count = 0
                        for name in names:
                            middle_name += name + ' '
                            count += 1
                            if count == len(names):
                                middle_name = middle_name[:-1]
                    try:
                        author = Author.objects.get(first_name__iexact=first_name, last_name__iexact=last_name)
                        if Book.objects.filter(title__iexact=title, author=author):
                            messages.error(request, 'Book already in database')
                            return redirect('add_book')
                    except Author.DoesNotExist:
                        if middle_name:
                            author = Author(first_name=first_name, middle_names=middle_name, last_name=last_name)
                        else:
                            author = Author(first_name=first_name, last_name=last_name)
                        # haven't saved the author yet

            # else no author has been selected or entered
            else:
                messages.error(request, 'No author selected or entered')
                return redirect('add_book')

            # at this point, we should have a title, and an author
            # rest is optional so we'll go through them

            other_authors = ''
            # if request.POST['other_authors']:
            #     other_authors = request.POST['other_authors']

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

            photo = None
            if request.FILES.get('photo', False):
                photo = request.FILES['photo']
                if photo.size > 1000000:
                    photo = None

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

            is_featured = False
            if request.POST.get('is_featured') == 'clicked':
                is_featured = True

            # now the adding stuff
            author.save()
            if series:
                series.save()

            book = Book.objects.create(
                title=title,
                author=author,
                other_authors=other_authors,
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
        else:
            messages.error(request, 'No title')
            return redirect('add_book')

    else:
        book_types = {
            'p': 'Paperback',
            'h': 'Hardcover',
            'o': 'Oversized',
        }
        authors = Author.objects.all()
        categories = Category.objects.all()
        series = Series.objects.all()
        tags = BookTags.objects.all()
        main_tags = BookTags.objects.filter(band=1)
        context = {
            'authors': authors,
            'categories': categories,
            'series': series,
            'tags': tags,
            'book_types': book_types,
            'main_tags': main_tags,
        }
        return render(request, 'books/add_book.html', context)


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
    num_results = len(books)

    paginator = Paginator(books, 24)
    page = request.GET.get('page')
    try:
        books = paginator.page(page)
    except PageNotAnInteger:
        # if page is not an intehger deliver the first page
        books = paginator.page(1)
    except EmptyPage:
        if request.is_ajax():
            # if the request is AJAX and the page is out of range
            # return an empty page
            return HttpResponse('')
        # if page is out of range deliver last page of results
        books = paginator.page(paginator.num_pages)
    
    #~~~~~~~~~~~~~
    # changed 'tags' to 'book_tags'
    all_tags = Book.book_tags.all()

    context = {
        'tag': tag,
        'all_tags': all_tags,
        'letter': letter,
        'books': books,
        'alphabet': a_z,
        'num_results': num_results,
    }

    if request.is_ajax():
        return render(request,
                      'books/books_filtered_ajax.html',
                      context)

    return render(request,
                  'books/books_filtered.html',
                  context)


    # # pagination
    # paginator = Paginator(books, 20)
    # page = request.GET.get('page')
    # paged_books = paginator.get_page(page)

    # context = {
    #     'tag': tag,
    #     'letter': letter,
    #     'books': paged_books,
    #     'alphabet': a_z,
    #     'num_results': num_results,
    # }
    # return render(request,
    #               'books/books_filtered.html',
    #               context)

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
# from django.contrib import messages
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
from common.decorators import ajax_required
@ajax_required
@login_required
@require_POST
def book_like(request):
    book_id = request.POST.get('id')
    action = request.POST.get('action')
    if book_id and action:
        try:
            book = Book.objects.get(id=book_id)
            if action == 'like':
                book.users_like.add(request.user)
            else:
                book.users_like.remove(request.user)
            return JsonResponse({'status':'ok'})
        except:
            pass
    return JsonResponse({'status':'error'})

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


# too much fiddly shit to get this editing review thing working
# best to change the add/edit review to a form,
# but not necessary from start.
# @login_required
# def edit_review(request, review, starting_point=None):

#     # if updating the review
#     if request.method == 'POST':

#         # perform checks
#         if request.POST.get('body'):
#             body = request.POST.get('body')

#             if request.POST.get('title'):
#                 title = request.POST.get('title')

#                 # rating - note, don't need to check if there is one,
#                 # cos default is set to None (0) so there will
#                 # always be a rating
#                 rating = int(request.POST.get('rating'))
#                 if rating == 0:
#                     rating = None

#                 # update review
#                 review.title = title
#                 review.body = body
#                 review.rating = rating
#                 review.save()

#                 messages.success(request, 'Your review for ' + review.book.title + ' has been updated')
#                 if starting_point == 'dashboard':
#                     return redirect(starting_point)
#                 else
#                     return redirect(review.book)

#             else:
#                 messages.error(request, 'You have not entered in a title')
#                 return redirect('add_review', book, body)

#         else:
#             messages.error(request, 'You have not entered in a review')
#             return redirect('add_review', book)

#     else:

#         values = {
#             'title': review.title,
#             'body': review.body,
#             'rating': review.rating,
#         }

#         rating_choices = {
#             '1':'Poor',
#             '2':'Average',
#             '3':'Good',
#             '4':'Very Good',
#             '5':'Excellent',
#         }
#         context = {
#             'book': book,
#             'rating_choices': rating_choices,
#             'values': values,
#         }
#         return render(request, 'books/edit_review.html', context)

from django.db.models import Q

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
        if self.request.FILES.get('photo'):
            photo = self.request.FILES['photo']
            if photo.size > 1000000:
                form.add_error('photo', 'Image file size exceeds the maximum limit of 1MB.')
                return self.form_invalid(form)

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
        if self.request.FILES.get('photo'):
            photo = self.request.FILES['photo']
            if photo.size > 1000000:
                form.add_error('photo', 'Image file size exceeds the maximum limit of 1MB.')
                return self.form_invalid(form)

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
def fetch_book_cover(isbn):
    """
    Fetches the cover image for a book using its ISBN from the Open Library API.

    Args:
        isbn (str): The ISBN of the book.

    Returns:
        bytes: The binary content of the book cover image if found, None otherwise.
    """
    url = f'https://openlibrary.org/search.json?isbn={isbn}'

    try:
        print(f'Fetching book cover for ISBN: {isbn}')
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        book_info = data.get('docs', [])
        if book_info:
            first_book = book_info[0]
            cover_edition_key = first_book.get('cover_edition_key')
            cover_i = first_book.get('cover_i')

            image_url = None
            if cover_edition_key:
                image_url = f'https://covers.openlibrary.org/b/olid/{cover_edition_key}-L.jpg'
            elif cover_i:
                image_url = f'https://covers.openlibrary.org/b/id/{cover_i}-L.jpg'
            
            if image_url:
                print(f"Downloading image from URL: {image_url}")
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                print(f'Size of image is: {len(response.content)}')
                return response.content
            else:
                print("No image URL found.")
                return None
        else:
            print("No book information found.")
            return None
    except Exception as e:
        print(f"Error fetching book data: {e}")
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
        messages.error(request, 'Unable to fetch image from API.')
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