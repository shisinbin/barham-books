from django.shortcuts import render
import random

from books.models import Book, Category
from authors.models import Author
from .forms import SearchForm
from staff.forms import AddBookCopy
from .fake_data import FAKE_REVIEWS, FAKE_COPIES

def index(request):
    return render(request, 'legacy/index.html')

def about(request):
	return render(request, 'legacy/about.html')

def books(request):
    categories = Category.objects.all()

    return render(request, 'legacy/books.html', { 'categories': categories })

def book(request):
    random_pool = list(Book.objects.order_by('?')[:25])

    fake_book = random_pool[0]

    fake_similar_books = random_pool[1:13]

    n = random.choice([0, 2, 4])
    fake_other_books_in_series = random_pool[13:13 + n]

    k = random.randint(0, len(FAKE_REVIEWS))
    fake_reviews = random.sample(FAKE_REVIEWS, k)

    context = {
        'book': fake_book,
        'copies': FAKE_COPIES,
        'other_books_in_series': fake_other_books_in_series,
        'similar_books': fake_similar_books,
        'reviews': fake_reviews,
        'available_copies': True,
        'has_not_reviewed': True,
        'is_recently_created': False,
        'legacy': True,
    }

    '''
    # LEGACY CODE
    
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
    '''

    return render(request, 'legacy/book.html', context)

def author(request):
    author = Author.objects.order_by('?').first()
    books = author.books.all()

    return render(request, 'legacy/author.html', {
        'author': author,
        'books': books,
    })