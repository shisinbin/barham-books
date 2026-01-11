from django.shortcuts import render, get_object_or_404
from .models import Author

def author(request, author_id, slug):
    author = get_object_or_404(Author, pk=author_id)
    books = author.books.order_by('title')
    num_books = books.count()

    context = {
        'author': author,
        'books': books,
        'hide_author': True,
        'num_books': num_books,
    }

    return render(request,'authors/author.html', context)

from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class AuthorUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Author
    fields = '__all__'

    def test_func(self):
        return self.request.user.is_staff