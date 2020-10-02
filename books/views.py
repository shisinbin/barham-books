from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .choices import language_choices, a_z
from django.contrib import messages
from taggit.models import Tag
from django.db.models import Count

from .models import Book, BookInstance2, Review, Category, BookTags
from .forms import SearchForm

from django.http import JsonResponse

def index(request):

    # autocomplete
    if 'term' in request.GET:
        term = request.GET.get('term')

        # dodgy way of overcoming the fact that books that
        # start with 'the' and 'a' is dodgy with searches
        if term.startswith('the '):
            term = term[4:]
        if term.startswith('a '):
            term = term[2:]
        if term != 'the' and len(term)>2:
            qs = Book.objects.filter(title__icontains=term)[:20]
            titles = list()
            for bk in qs:
                titles.append(bk.title)
            return JsonResponse(titles, safe=False)

    # options are .all(), .order_by('some_field'), or .filter()
    # NOTE: not using this at the moment, maybe later so leaving it
    #featured_books = Book.objects.filter(is_featured=True)[:4]

    categories = Category.objects.all()

    form = SearchForm()

    context = {
        #'featured_books': featured_books,
        # 'language_choices': language_choices,
        'form': form,
        'categories': categories,
    }

    return render(request, 'books/books.html', context)

from reservations.models import Reservation

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

    context = {
        'book': book,
        'copies': copies,
        'available_copies': available_copies,
        'reviews': reviews,
        'has_not_reviewed': has_not_reviewed,
        'other_books_in_series': other_books_in_series,
        'similar_books': similar_books,
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

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class BookUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    fields = '__all__'

    def test_func(self):
        return self.request.user.is_staff


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
                return redirect('book', book.id, book.slug)

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
    books = Book.objects.all()
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
                            SearchVector('author__first_name', weight='B') + \
                            SearchVector('series__name', weight='B')
            search_query = SearchQuery(query)
            results = Book.objects.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
                ).filter(rank__gte=0.3).order_by('-rank')

            ####
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
#                     return redirect('book', review.book.id, book.slug)

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

from authors.models import Author
from books.models import Series
from django.db.models import Q

def category(request, category_code):
    categories = Category.objects.all()
    category = get_object_or_404(Category, code=category_code)
    category_books = Book.objects.filter(category=category)
    featured_books = category_books.filter(is_featured=True)
    
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
    }
    return render(request, 'books/category.html', context)