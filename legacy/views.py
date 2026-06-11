import random
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import Lower
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.auth.models import User
from books.models import Book, Category, BookTags, Series
from authors.models import Author
# from .forms import SearchForm
# from staff.forms import AddBookCopy
from .fake_data import FAKE_REVIEWS, FAKE_COPIES
from .choices import a_z, language_choices

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

    return render(request, 'legacy/book.html', context)

def author(request):
    author = Author.objects.order_by('?').first()
    books = author.books.all()

    return render(request, 'legacy/author.html', {
        'author': author,
        'books': books,
    })

def books_filtered(request, letter_choice=None, tag_slug=None):
    books = Book.objects.filter(instances__isnull=False).distinct()

    tag = None
    letter = None

    # two ways of filtering - tag or letter
    if tag_slug:
        tag = get_object_or_404(BookTags, slug=tag_slug)
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
    
    all_tags = Book.book_tags.all()

    context = {
        'tag': tag,
        'all_tags': all_tags,
        'letter': letter,
        'books': paged_books,
        'alphabet': a_z,
        'num_results': num_results,
        'legacy': True,
    }

    return render(request,
                  'legacy/books_filtered.html',
                  context)

def filter_by_tags(request):
    tags = Book.book_tags.all()

    dropdown_tags = tags.order_by('name')

    tags_popular = (
        tags
        .annotate(num_times=Count('book_tags'))
        .order_by('-num_times')[:50]
    )

    context = {
        'tags': tags,
        'tags_popular': tags_popular,
        'dropdown_tags': dropdown_tags,
        'legacy': True,
    }

    return render(request, 'legacy/tags.html', context)

def tag_search(request):
    queryset_list = Book.objects.all()
    selected_tags = []
    tag_strings = []
    search_path = 'tag_search?'

    if 'tag' in request.GET:
        tag_strings = request.GET.getlist('tag')

        for tag_string in tag_strings:
            search_path = search_path + 'tag=' + tag_string + '&'

            tag = get_object_or_404(BookTags, name=tag_string)
            selected_tags.append(tag)

            queryset_list = queryset_list.filter(book_tags__in=[tag])

    if 'language' in request.GET:
        language = request.GET['language']
        search_path = search_path + 'language=' + language

        if language != 'any':
            queryset_list = queryset_list.filter(language__icontains=language)

    queryset_list = queryset_list.distinct()

    num_results = queryset_list.count()

    paginator = Paginator(queryset_list, 30)
    page = request.GET.get('page')
    paged_books = paginator.get_page(page)

    tags = Book.book_tags.order_by('name')

    context = {
        'tags': tags,
        'selected_tags': selected_tags,
        'tag_strings': tag_strings,
        'num_results': num_results,
        'language_choices': language_choices,
        'books': paged_books,
        'values': request.GET,
        'search_path': search_path,
        'legacy': True,
    }

    return render(request, 'legacy/tag_search.html', context)

def category(request):
    categories = Category.objects.all()

    category = get_object_or_404(Category, code="GEN")

    category_books = Book.objects.filter(category=category)
    featured_books = category_books.filter(is_featured=True)

    if len(featured_books) % 4 == 0:
        num_slides = int(len(featured_books) / 4)
    else:
        num_slides = int(len(featured_books) // 4) + 1
    
    num_slides_string = ''
    for i in range(num_slides):
        num_slides_string = num_slides_string + str(i)

    popular_authors = (
        Author.objects
        .annotate(num_times=Count('books', filter=Q(books__in=category_books)))
        .order_by('-num_times')[:10]
    )
        
    series_with_multiple_books = (
        Series.objects
        .annotate(num_times=Count('books', filter=Q(books__in=category_books)))
        .order_by('-num_times')[:10]
    ) 

    context = {
        'category': category,
        'categories': categories,
        'category_books': category_books,
        'featured_books': featured_books,
        'popular_authors': popular_authors,
        'series_with_multiple_books': series_with_multiple_books,
        'num_slides_string': num_slides_string,
        'legacy': True,
    }
    return render(request, 'legacy/category.html', context)

@staff_member_required
def users(request):
    users = User.objects.order_by(Lower('username'))

    print(f"Value of keyword parameter: '{request.GET.get('keyword')}'")

    keyword = request.GET.get('keyword', '').strip()

    if keyword:
        users_username = users.filter(username__icontains=keyword)
        users_last_name = users.filter(last_name__icontains=keyword)
        users = (users_username | users_last_name).distinct()

    # pagination
    paginator = Paginator(users, 10)
    page = request.GET.get('page')
    paged_users = paginator.get_page(page)

    context = {
        'users': paged_users,
        'query': keyword,
    }
    
    return render(request, 'legacy/users.html', context)

@staff_member_required
def add_book(request):
    book_types = {
        'p': 'Paperback',
        'h': 'Hardcover',
        'o': 'Oversized',
    }

    context = {
        'authors': Author.objects.all(),
        'categories': Category.objects.all(),
        'series': Series.objects.all(),
        'book_types': book_types,
        'main_tags': BookTags.objects.filter(band=1),
        'form_data': {},
        'selected_tags': [],
        'legacy': True,
    }

    return render(request, 'legacy/add_book.html', context)