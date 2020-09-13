from django.contrib import admin

from .models import Book, BookInstance2, Review, Series
from taggit.models import Tag

class BookInstance2Inline(admin.TabularInline):
	model = BookInstance2
	extra = 0
	# readonly_fields = ('id', 'pages', 'publisher')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
	list_display = ('id', 'title', 'slug', 'author', 'tags', 'is_featured')
	list_display_links = ('id', 'title')
	list_editable = ('is_featured',)
	search_fields = ('title',)
	list_per_page = 50
	inlines = [BookInstance2Inline]

@admin.register(BookInstance2)
class BookInstance2Admin(admin.ModelAdmin):
	list_filter = ('status', 'due_back')
	list_display = ('id', 'book', 'status', 'due_back') #'id'
	list_display_links = ('id', 'book')

	# how and what fields appear in the add book instance page
	fieldsets = (
		(None, {
			'fields': ('book', 'publisher', 'pages') # 'id'
			}),
		('Availability', {
			'fields': ('status', 'due_back', 'borrower')
			}),
		('Extra', {
			'fields': ('isbn10', 'isbn13', 'book_type')
			}),
		)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('title', 'user', 'book', 'created', 'active')
	list_filter = ('active', 'created', 'updated')
	search_fields = ('user', 'book', 'body')

class BookInline(admin.TabularInline):
	model = Book
	extra = 0
	exclude = ['other_authors', 'summary', 'tags', 'user_tags', 'language', 'publish_date', 'isbn_latest', 'photo', 'is_featured']
	readonly_fields = ('author', 'title')

@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
	inlines = [BookInline]