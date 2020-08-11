from django.shortcuts import render
from books.choices import genre_choices, language_choices

from books.models import Book
from blog.models import Post

def index(request):
	# books = Book.objects.filter(is_featured=True)[:3]
	latest_posts = Post.published.all()[:3]

	context = {
		#'books': books,
		'latest_posts': latest_posts,
		'genre_choices': genre_choices,
		'language_choices': language_choices,
	}

	return render(request, 'pages/index.html', context)

def about(request):
	return render(request, 'pages/about.html')