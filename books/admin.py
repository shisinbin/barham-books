import csv
import datetime

from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponse

from .models import Book, BookInstance2, BookTags, BookInterest, Review, Series, Category


def export_book_copies_to_csv(modeladmin, request, queryset):
    date = datetime.date.today()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=book_copies_{date}.csv'

    writer = csv.writer(response)

    writer.writerow([
        'book_id',
        'copy_id',
        'title',
        'author',
        'category',
        'series',
        'series_number',
        'year',
        'isbn10',
        'isbn13',
        'publisher',
        'pages',
        # 'format',
        'tags',
        'book_url',
    ])

    queryset = (
        queryset
        .select_related('book', 'book__author', 'book__category', 'book__series')
        .prefetch_related('book__book_tags')
    )

    for copy in queryset:
        book = copy.book
        tags = ', '.join(tag.name for tag in book.book_tags.all()) if book else ''

        writer.writerow([
            book.id if book else '',
            copy.id,
            book.title if book else '',
            book.author if book and book.author else '',
            book.category if book and book.category else '',
            book.series if book and book.series else '',
            book.series_num if book else '',
            book.year if book else '',
            copy.isbn10 or '',
            copy.isbn13 or '',
            copy.publisher or '',
            copy.pages or '',
            # copy.get_book_type_display() if copy.book_type else '',
            tags,
            book.get_absolute_url() if book else '',
        ])

    return response

export_book_copies_to_csv.short_description = 'Export selected book copies to CSV'


class BookInstance2Inline(admin.TabularInline):
    model = BookInstance2
    extra = 0
    fields = ('publisher', 'pages', 'isbn10', 'isbn13', 'book_type')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'slug', 'author', 'category',)
    list_display_links = ('id', 'title')
    list_filter = ('category', 'is_featured', 'created')
    search_fields = ('title',)
    list_per_page = 50
    readonly_fields = ('slug', 'created', 'updated')
    inlines = [BookInstance2Inline]

@admin.register(BookInstance2)
class BookInstance2Admin(admin.ModelAdmin):
    list_display = ('id', 'book', 'isbn10', 'isbn13', 'publisher')
    list_display_links = ('id', 'book')
    search_fields = ('book__title', 'isbn10', 'isbn13')
    actions = [export_book_copies_to_csv]

    fieldsets = (
        (None, {
            'fields': ('book', 'publisher', 'pages')
        }),
        ('Extra', {
            'fields': ('isbn10', 'isbn13', 'book_type')
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'book', 'created', 'active')
    list_filter = ('active', 'created', 'updated')
    search_fields = ('title', 'body', 'user__username', 'book__title')

class BookInlineForSeries(admin.TabularInline):
    model = Book
    extra = 0
    fields = ('title', 'author', 'category', 'series_num')
    readonly_fields = ('author', 'title', 'category', 'series_num')
    can_delete = False
    show_change_link = True

@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    inlines = [BookInlineForSeries]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'code')
    readonly_fields = ('tag_summary',)

    def tag_summary(self, obj):
        tags = (
            BookTags.objects
            .filter(book_tags__content_object__category=obj)
            .distinct()
            .order_by('band', 'name')
            .values_list('name', flat=True)
        )
        return ', '.join(tags) or '—'

    tag_summary.short_description = 'Tags used by books in this category'

@admin.register(BookTags)
class BookTagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'band')
    list_filter = ('band',)
    search_fields = ('name',)

@admin.register(BookInterest)
class BookInterestAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'created', 'handled')
    list_filter = ('handled', 'created')
    search_fields = ('book__title', 'user__username', 'user__email')


# ------------- Books for sale -----------------
from .models import BookForSale, SaleCategory

@admin.register(BookForSale)
class BookForSaleAdmin(admin.ModelAdmin):
    # list_display = ('slug', 'title', 'author')
    # prepopulated_fields = { 'slug': ('title',)}
    readonly_fields = ('slug',)
    search_fields = ('title', 'author__first_name', 'author__last_name')

@admin.register(SaleCategory)
class SaleCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name',)