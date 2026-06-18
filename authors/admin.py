from django.contrib import admin

from .models import Author
from books.models import Book, BookForSale

class BooksInline(admin.TabularInline):
	model = Book
	fields = ['title', 'year']
	readonly_fields = ('title', 'year')
	extra = 0
	show_change_link = True
	can_delete = False

class BooksForSaleInline(admin.TabularInline):
	model = BookForSale
	fields = ['title', 'sale_category']
	readonly_fields = ('title', 'sale_category')
	extra = 0
	show_change_link = True
	can_delete = False

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('id', 'formal_name', 'slug', 'dob', 'dod')
    list_display_links = ('formal_name',)
    fields = [
        ('first_name', 'middle_names', 'last_name'),
        'slug',
        'biography',
        ('dob', 'dod'),
        'photo',
    ]
    readonly_fields = ('slug',)
    inlines = [BooksInline, BooksForSaleInline]
    list_per_page = 50
    search_fields = ('last_name', 'middle_names', 'first_name')

    def formal_name(self, obj):
        return obj.formal()

    formal_name.short_description = "Author"
    formal_name.admin_order_field = "last_name"