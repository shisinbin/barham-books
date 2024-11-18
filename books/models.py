from django.db import models
from django.contrib.auth.models import User

from datetime import date
from django.utils import timezone

from authors.models import Author

import os
from django.conf import settings
from django.urls import reverse

from django.utils.text import slugify
from django.core.files.storage import default_storage

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase, TagBase, ItemBase

from easy_thumbnails.files import get_thumbnailer

import logging

logging.basicConfig(
    filename=os.path.join(settings.BASE_DIR, 'upload_location_debug.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

def upload_location(instance, filename):
    if '.' in filename:
        ext = filename.split('.')[-1]
    else:
        ext = 'jpg' # Default to jpg if no extension provided

    if instance.title:
        truncated_title = slugify(instance.title[:40])
        new_filename = f"books/{instance.title[:1].upper()}/{truncated_title}-{slugify(instance.author.last_name)}.{ext}"
    else:
        new_filename = f"books/{filename}"

    # Full path for new image
    new_image_path = os.path.join(settings.MEDIA_ROOT, new_filename)
    logging.debug(f"New image path: {new_image_path}")

    if instance.pk: # Only applicable to updates

        if instance.photo and instance.photo.name:
            logging.debug(f"Old image name: {instance.photo.name}")
            old_image_rel_path = f"books/{instance.title[:1].upper()}/{instance.photo.name}"
            old_image_path = os.path.join(settings.MEDIA_ROOT, old_image_rel_path)
            logging.debug(f"Old image full path: {old_image_path}")

            if old_image_path != new_image_path:
                old_thumbnail_path = f"{old_image_path}.100x0_q85.jpg"
                logging.debug(f"Old thumbnail path: {old_thumbnail_path}")

                if os.path.exists(old_thumbnail_path):
                    os.remove(old_thumbnail_path)
                    logging.info(f"Deleted old thumbnail: {old_thumbnail_path}")
                else:
                    logging.warning(f"Thumbnail not found: {old_thumbnail_path}")

        # Remove any file already occupying the new image path
        if os.path.exists(new_image_path):
            os.remove(new_image_path)
            logging.info(f"Deleted pre-existing file at new image path: {new_image_path}")

    return new_filename

# iterates through all book_tags belonging to a book
# and checks to see if that tag is in the arrayfield 'tags_included' -
# (basically a list of all book_tags in books belonging to category)
# if it isn't, then it adds the book_tag's name(so just a string)
# to the arrayfield
def update_tags_in_categories(book):
    if book.category:
        category = book.category

        # redundant check now that I've changed the default=list on this tags_included field in Category class
        if category.tags_included is None:
            category.tags_included = []

        if book.book_tags.all():
            for tag in book.book_tags.all():
                if (tag.name not in category.tags_included) and (len(tag.name) <= 30):
                    #print('adding ' + tag.name + ' to ' + category.name)
                    category.tags_included.append(tag.name)
                    category.tags_included.sort()
                    category.save()


class Series(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'series'
    def __str__(self):
        return self.name
    def get_all_tags(self):
        tag_set = set()
        for book in self.books.all():
            for tag in book.book_tags.all():
                tag_set.add(tag)
        return tag_set
    # def formal(self):
    #     if self.name.startswith(('the ', 'The ')):
    #         return self.name[4:] + ', The'
    #     else:
    #         return self.name

class TaggedBook(TaggedItemBase):
    content_object = models.ForeignKey('Book',
                                       on_delete=models.CASCADE)

from django.contrib.postgres.fields import ArrayField
# class PrimaryTags(TagBase):
#     # categories = ArrayField(
#     #                 models.CharField(max_length=3),
#     #                 blank=True, null=True
#     #                 )
#     class Meta:
#         verbose_name = "Primary Tag"
#         verbose_name_plural = "Primary Tags"

# class BookPrimaryTag(ItemBase):
#     content_object = models.ForeignKey('Book',
#                                        on_delete=models.CASCADE)
#     tag = models.ForeignKey(
#             PrimaryTags,
#             on_delete=models.CASCADE,
#             related_name="book_primary_tags")

# class SecondaryTags(TagBase):
#     # categories = ArrayField(
#     #                 models.CharField(max_length=3),
#     #                 blank=True, null=True
#     #                 )
#     class Meta:
#         verbose_name = "Secondary Tag"
#         verbose_name_plural = "Secondary Tags"

# class BookSecondaryTag(ItemBase):
#     content_object = models.ForeignKey('Book',
#                                        on_delete=models.CASCADE)
#     tag = models.ForeignKey(
#             SecondaryTags,
#             on_delete=models.CASCADE,
#             related_name="book_secondary_tags")


# class UserTaggedBook(TaggedItemBase):
#     content_object = models.ForeignKey('Book',
#                                        on_delete=models.CASCADE)
#     tagger = models.ForeignKey(User,
#                                related_name='book_tags',
#                                on_delete=models.DO_NOTHING,
#                                null=True,
#                                blank=True)

class BookTags(TagBase):

    BANDS = (
        (1, 'General fiction main'),
        (2, 'General fiction secondary'),
        (3, 'Non-fiction'),
        (4, 'Sci-fi and Fantasy'),
        (5, 'Children and Middle Grade'),
        (6, 'Teen and Young adult'),
    )

    band = models.PositiveIntegerField(
        choices=BANDS,
        blank=True,
        default=99,
        help_text='Tag Band'
    )
    class Meta:
        verbose_name = "book tag"
        verbose_name_plural = "book tags"
        ordering = ('band', 'name',)

class BookTag(ItemBase):
    content_object = models.ForeignKey('Book',
                                       on_delete=models.CASCADE)
    tag = models.ForeignKey(
            BookTags,
            on_delete=models.CASCADE,
            related_name="book_tags")
    
class SaleCategory(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)  # For URL/slugs or other use
    description = models.TextField(max_length=1000, blank=True)

    class Meta:
        verbose_name_plural = 'Sale Categories'

    def __str__(self):
        return self.name
    
class BookForSale(models.Model):
    title = models.CharField(max_length=250, db_index=True)
    author = models.ForeignKey(Author,
                               related_name='books_for_sale',
                               on_delete=models.SET_NULL,
                               null=True)
    summary = models.TextField(max_length=2000, blank=True)
    isbn = models.CharField(max_length=13, blank=True, null=True)
    slug = models.SlugField(max_length=250,
                            null=False,
                            unique=True)
    sale_category = models.ForeignKey(SaleCategory,
                                      related_name='books',
                                      on_delete=models.SET_NULL,
                                      null=True,
                                      blank=True)
    price = models.DecimalField(max_digits=10,
                                decimal_places=2,
                                null=True,
                                blank=True)
    is_sold = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='books_for_sale/', blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('title',)
        verbose_name_plural = 'books for sale'
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("book_for_sale_detail", kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug or self.title != BookForSale.objects.get(pk=self.pk).title:
            original_slug = slugify(self.title, allow_unicode=True)
            slug = original_slug
            # Check for conflicts
            num = 1
            while BookForSale.objects.filter(slug=slug).exists():
                slug = f'{original_slug}-{num}'
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)
    

class Book(models.Model):
    author = models.ForeignKey(Author,
                               related_name='books',
                               on_delete=models.SET_NULL,
                               null=True)
    other_authors = models.CharField(max_length=600,
                                     blank=True)
    title = models.CharField(max_length=250, db_index=True)
    summary = models.TextField(max_length=2000,
                               blank=True)
    slug = models.SlugField(max_length=250,
                            default='',
                            editable=False)
    tags = TaggableManager(through=TaggedBook,
                           blank=True)

    book_tags = TaggableManager(through=BookTag,
                                blank=True,
                                verbose_name='book tags')

    # primary and secondary tags
    # primary_tags = TaggableManager(through=BookPrimaryTag,
    #                                blank=True,
    #                                verbose_name='primary tags')
    # secondary_tags = TaggableManager(through=BookSecondaryTag,
    #                                blank=True,
    #                                verbose_name='secondary tags')

    # user_tags = TaggableManager(through=UserTaggedBook,
    #                             related_name='user_tags',
    #                             blank=True,
    #                             verbose_name="user tags")
    language = models.CharField(max_length=200,
                                default='English')
    publish_date = models.DateField(blank=True,
                                    null=True)
    users_like = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                        related_name='books_liked',
                                        blank=True)
    photo = models.ImageField(upload_to=upload_location,
                              blank=True)
    is_featured = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    series = models.ForeignKey(Series,
                               related_name='books',
                               on_delete=models.SET_NULL,
                               null=True,
                               blank=True)
    series_num = models.PositiveIntegerField(blank=True, null=True)
    category = models.ForeignKey('Category',
                                 related_name='books',
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 blank=True)
    year = models.PositiveIntegerField(blank=True,
                                       null=True,
                                       verbose_name='original publication year')

    class Meta:
        ordering = ('title',)

    def get_absolute_url(self):
        """Returns the url to access a detail record for this book."""
        return reverse('book',
                       args=[str(self.id),
                             self.slug])
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)
        update_tags_in_categories(self)


    def __str__(self):
        return self.title
    # def get_cover_url(self):
    #     if self.isbn_latest:
    #         return 'http://covers.openlibrary.org/b/isbn/' + self.isbn_latest + '-M.jpg'
    #     else:
    #         return None


#import uuid
# ###### this is the corrupted model #######
# class BookInstance(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     book = models.ForeignKey('Book', on_delete=models.CASCADE, null=True)
#     pages = models.IntegerField(blank=True)
#     publisher = models.CharField(max_length=200)
#     due_back= models.DateField(null=True, blank=True)
#     LOAN_STATUS = (
#         ('m', 'Maintenance'),
#         ('o', 'On loan'),
#         ('a', 'Available'),
#         ('r', 'Reserved'),
#     )
#     status = models.CharField(
#         max_length=1,
#         choices=LOAN_STATUS,
#         blank=True,
#         default='a',
#     )
#     borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     created = models.DateTimeField(auto_now_add=True)
#     updated = models.DateTimeField(auto_now=True)
# ############################################################
#     @property
#     def is_overdue(self):
#         if self.due_back and date.today() > self.due_back:
#             return True
#         return False
# ####################################################################
#     class Meta:
#         ordering = ['due_back']
#         # permissions = (("can_mark_returned", "Set book as returned"),)
# ##################################################################
#     def __str__(self):
#         """String for representing the Model object."""
#         return f'{self.id}' # ({self.book.title})'
# #########################################################

class BookInstance2(models.Model):
    book = models.ForeignKey('Book',
                             related_name="instances",
                             on_delete=models.CASCADE,
                             null=True)
    pages = models.IntegerField(blank=True, null=True)
    isbn10 = models.CharField(max_length=10, blank=True, null=True)
    isbn13 = models.CharField(max_length=13, blank=True, null=True, db_index=True)
    publisher = models.CharField(max_length=200, blank=True)
    due_back= models.DateField(null=True, blank=True)
    BOOK_TYPE_CHOICES = (
        ('p', 'Paperback'),
        ('h', 'Hardcover'),
        ('o', 'Oversized'),
    )
    book_type = models.CharField(
        max_length=1,
        choices=BOOK_TYPE_CHOICES,
        blank=True,
        default='p',
    )
    LOAN_STATUS = (
        ('m', 'Maintenance'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )
    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        blank=True,
        default='a',
        db_index=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def is_overdue(self):
        if self.due_back and date.today() > self.due_back:
            return True
        return False

    class Meta:
        ordering = ['status', 'book__title']
        verbose_name = 'Book Instance'
        # permissions = (("can_mark_returned", "Set book as returned"),)

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.book.title} (#{self.id})'
    def get_formatted_isbn10(self):
        i = self.isbn10
        if len(i) == 10:
            return f"{i[0]}-{i[1:4]}-{i[4:9]}-{i[-1]}"
        else:
            return self.isbn10
    def get_formatted_isbn13(self):
        i = self.isbn13
        if len(i) == 13:
            return f"{i[:3]}-{i[3:5]}-{i[5:10]}-{i[10:12]}-{i[-1]}"
        else:
            return self.isbn13

class Review(models.Model):
    book = models.ForeignKey('Book', on_delete=models.DO_NOTHING, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    title = models.CharField(max_length=50, default='add title')
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True,)
    active = models.BooleanField(default=True)
    RATING_CHOICES = (
      (1, 'Poor'),
      (2, 'Average'),
      (3, 'Good'),
      (4, 'Very Good'),
      (5, 'Excellent'),
    )
    rating = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True)
    class Meta:
        ordering = ('created',)
    def __str__(self):
        return f"Review by {self.user} on {self.book}"

from django.contrib.postgres.fields import ArrayField
class Category(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20)
    code = models.CharField(max_length=3, unique=True)
    order = models.PositiveIntegerField(unique=True)
    description = models.TextField(max_length=2000,
                                   blank=True)
    tags_included = ArrayField(
                    models.CharField(max_length=30),
                    blank=True, default=list
                    )

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'categories'
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse('category',
                       args=[self.code])

def update_tags_in_cat_globally():
    # flush the arrayfields
    for cat in Category.objects.all():
        cat.tags_included.clear()
        cat.save()
    # then grind through every book - 
    # could do this for a category instead to save cpu
    for book in Book.objects.all():
        update_tags_in_categories(book)


# class SubCategory(models.Model):
#     name = models.CharField(max_length=100)
#     code = models.CharField(max_length=3, unique=True)

#     class Meta:
#         verbose_name_plural = 'subcategories'
#     def __str__(self):
#         return self.name