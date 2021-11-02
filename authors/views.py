from django.shortcuts import render, get_object_or_404
from .models import Author

def author(request, author_id, slug):
    author = get_object_or_404(Author, pk=author_id)
    books = author.books.order_by('-year')

    context = {
        'author': author,
        'books': books,
    }

    return render(request,
                  'authors/author.html',
                  context)