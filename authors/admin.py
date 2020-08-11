from django.contrib import admin

from .models import Author
from books.models import Book

class BooksInline(admin.TabularInline):
	model = Book
	#exclude = ['other_authors', 'summary', 'language', 'isbn', 'photo', 'is_featured']
	fields = ['title', 'genre', 'publish_date', 'isbn']
	readonly_fields = ('title', 'genre', 'publish_date')
	extra = 0
	show_change_link = True
	can_delete = False

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
	list_display = ('last_name', 'slug', 'first_name', 'dob', 'dod', 'is_featured')
	# how and what fields appear in the add author page
	fields = [('first_name', 'middle_names', 'last_name'), 'biography', ('dob', 'dod'), ('photo', 'is_featured')]
	inlines = [BooksInline]
	list_per_page = 10
	search_fields = ('last_name', 'middle_names', 'first_name')