from django.shortcuts import render, redirect
from books.choices import language_choices

#from books.models import Book
from blog.models import Post

def index(request):
	# redirecting home page to books
	# if 1 == 1:
	# 	return redirect('books')
	# else:
	# 	# books = Book.objects.filter(is_featured=True)[:3]
	# 	latest_posts = Post.published.all()[:3]

	# 	context = {
	# 		#'books': books,
	# 		'latest_posts': latest_posts,
	# 		'language_choices': language_choices,
	# 	}

	# 	return render(request, 'pages/index.html', context)
	return render(request, 'pages/index.html')

def about(request):
	return render(request, 'pages/about.html')