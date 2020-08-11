from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .choices import language_choices, a_z
from django.contrib import messages
from taggit.models import Tag

from .models import Book, BookInstance2, Genre, Review

def index(request):
    # options are .all(), .order_by('some_field'), or .filter()
    books = Book.objects.filter(is_featured=True)[:4]

    paginator = Paginator(books, 6)
    page = request.GET.get('page')
    paged_books = paginator.get_page(page)

    genres = Genre.objects.all()
    featured_genres = genres.filter(is_featured=True)[:8]

    context = {
        'books': paged_books,
        'language_choices': language_choices,
        'genres': genres,
        'featured_genres': featured_genres,
    }

    return render(request, 'books/books.html', context)


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

    if book.genre:
        try:
            genre = Genre.objects.get(name=book.genre)
        except Exception:
            genre = None
    else:
        genre = None

    # review stuff
    reviews = Review.objects.filter(book=book)
    has_not_reviewed = True
    if request.user.is_authenticated:
        if reviews.filter(user=request.user):
            has_not_reviewed = False

    context = {
        'book': book,
        'genre': genre,
        'copies': copies,
        'available_copies': available_copies,
        'reviews': reviews,
        'has_not_reviewed': has_not_reviewed,
    }

    return render(request, 'books/book.html', context)


def search(request):
    queryset_list = Book.objects.all()
    too_short = False

    # title
    if 'title' in request.GET:
        title = request.GET['title']
        if title:
            if len(title) < 3:
                too_short = True
            else:
                queryset_list = queryset_list.filter(title__icontains=title)

    if too_short:
        queryset_list = None
        paged_books = queryset_list
    else:
        if 'surname' in request.GET:
            surname = request.GET['surname']
            if surname:
                if len(surname) > 2:
                    queryset_list = queryset_list.filter(author__last_name__iexact=surname)

        # isbn
        if 'isbn' in request.GET:
            isbn = request.GET['isbn']
            if isbn:
                queryset_list = queryset_list.filter(isbn__iexact=isbn)

        # genre
        if 'genre' in request.GET:
            genre = request.GET['genre']
            if genre and not genre == 'Genre (Any)':
                queryset_list = queryset_list.filter(genre__name__iexact=genre)

        # genre
        if 'language' in request.GET:
            language = request.GET['language']
            if language and not language == 'Language (Any)':
                queryset_list = queryset_list.filter(language__icontains=language)
        
        num_results = queryset_list.count()

        paginator = Paginator(queryset_list, 8)
        page = request.GET.get('page')
        paged_books = paginator.get_page(page)

    genres = Genre.objects.order_by('name')

    context = {
        'num_results': num_results,
        'language_choices': language_choices,
        'genres': genres,
        'books': paged_books,
        'values': request.GET, # this is for getting the search terms to show up in the search results page
    }
    return render(request, 'books/search.html', context)


def genre(request, genre_id):
    genre = Genre.objects.get(id=genre_id)
    books_in_genre = Book.objects.filter(genre=genre)

    featured_books = books_in_genre.filter(genre_featured=True)[:4]
    non_featured_books = books_in_genre.filter(genre_featured=False)

    paginator = Paginator(non_featured_books, 8)
    page = request.GET.get('page')
    paged_books = paginator.get_page(page)

    context = {
        'genre': genre,
        'books': paged_books,
        'featured_books': featured_books,
    }

    return render(request, 'books/genre.html', context)

from django.views.generic.edit import CreateView, UpdateView, DeleteView


class BookUpdate(UpdateView):
    model = Book
    fields = '__all__'


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

def add_review(request, book_id, body=None):
    book = Book.objects.get(id=book_id)
    if request.method == 'POST':

        # perform checks
        if request.POST.get('body'):
            body = request.POST.get('body')

            if request.POST.get('title'):
                title = request.POST.get('title')

                # add review
                user = request.user
                review = Review(
                    book=book,
                    user=user,
                    title=title,
                    body=body,
                    )
                review.save()

                messages.success(request, 'Your review has been posted')
                return redirect('book', book.id)

            else:
                messages.error(request, 'You have not entered in a title')
                return redirect('add_review', book, body)

        else:
            messages.error(request, 'You have not entered in a review')
            return redirect('add_review', book)

    else:
        return render(request, 'books/add_review.html', {'book': book})

def books_filtered(request, letter_choice=None, tag_slug=None):
    books = Book.objects.all()
    tag = None
    letter = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        books = books.filter(tags__in=[tag])
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

    paginator = Paginator(books, 20)
    page = request.GET.get('page')
    paged_books = paginator.get_page(page)

    context = {
        'tag': tag,
        'letter': letter,
        'books': paged_books,
        'alphabet': a_z,
    }
    return render(request,
                  'books/books_filtered.html',
                  context)