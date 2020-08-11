from django.db import models
from django.contrib.auth.models import User

from datetime import date
from django.utils import timezone

from authors.models import Author

import os
from django.conf import settings
from django.urls import reverse

from django.utils.text import slugify

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

def upload_location(instance, filename):
    ext = filename.split('.')[-1]
    if instance.title:
        new_filename = f"books/{instance.title[:1].upper()}/{instance.title}.{ext}"
    else:
        new_filename = filename
    return os.path.join(settings.MEDIA_ROOT, new_filename)

def upload_genre_location(instance, filename):
    ext = filename.split('.')[-1]
    if instance.name:
        new_filename = f"genres/{instance.name}.{ext}"
    else:
        new_filename = filename
    return os.path.join(settings.MEDIA_ROOT, new_filename)


class TaggedBook(TaggedItemBase):
    content_object = models.ForeignKey('Book',
                                       on_delete=models.CASCADE)

class UserTaggedBook(TaggedItemBase):
    content_object = models.ForeignKey('Book',
                                       on_delete=models.CASCADE)
    tagger = models.ForeignKey(User,
                               related_name='book_tags',
                               on_delete=models.DO_NOTHING,
                               null=True,
                               blank=True)

class Book(models.Model):
    author = models.ForeignKey(Author,
                               related_name='books',
                               on_delete=models.SET_NULL,
                               null=True)
    other_authors = models.CharField(max_length=600,
                                     blank=True)
    title = models.CharField(max_length=250)
    summary = models.TextField(max_length=2000,
                               blank=True)
    slug = models.SlugField(max_length=250,
                            default='',
                            editable=False)
    #primary_genre = models.ForeignKey('Genre', on_delete=models.SET_NULL, null=True, blank=True)
    tags = TaggableManager(through=TaggedBook,
                           blank=True)
    user_tags = TaggableManager(through=UserTaggedBook,
                                related_name='user_tags',
                                blank=True)
    genre = models.ForeignKey('Genre',
                              on_delete=models.SET_NULL,
                              null=True,
                              blank=True)
    #other_genres = models.ManyToManyField('Genre', blank=True)
    language = models.CharField(max_length=200,
                                default='English')
    #language = models.ForeignKey('Language', on_delete=models.SET_NULL, null=True)
    publish_date = models.DateField(blank=True,
                                    null=True)


    # the folling field has been set to None for all objects
    isbn_latest = models.CharField(max_length=13, blank=True, null=True)
    



    photo = models.ImageField(upload_to=upload_location,
                              blank=True)
    is_featured = models.BooleanField(default=False)
    genre_featured = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ('title',)

    def get_absolute_url(self):
        """Returns the url to access a detail record for this book."""
        return reverse('book',
                       args=[str(self.id),
                             self.slug])
    def save(self, *args, **kwargs):
        value = self.title
        self.slug = slugify(value, allow_unicode=True)
        super().save(*args, **kwargs)
    
    # def display_genre(self):
    #   return ', '.join(genre.name for genre in self.genres.all()[:])

    # display_genre.short_descriptions = 'Genre'

    def __str__(self):
        return self.title
    def get_cover_url(self):
        if self.isbn_latest:
            return 'http://covers.openlibrary.org/b/isbn/' + self.isbn_latest + '-M.jpg'
        else:
            return None


import uuid

###### this is the corrupted model #######
class BookInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    book = models.ForeignKey('Book', on_delete=models.CASCADE, null=True)
    pages = models.IntegerField(blank=True)
    publisher = models.CharField(max_length=200)
    due_back= models.DateField(null=True, blank=True)
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
    )
    borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
############################################################
    @property
    def is_overdue(self):
        if self.due_back and date.today() > self.due_back:
            return True
        return False
####################################################################
    class Meta:
        ordering = ['due_back']
        # permissions = (("can_mark_returned", "Set book as returned"),)
##################################################################
    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id}' # ({self.book.title})'
#########################################################


class Genre(models.Model):
    name = models.CharField(max_length=200)
    photo = models.ImageField(upload_to=upload_genre_location, blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# class Language(models.Model):
#   name = models.CharField(max_length=200)
#   def __str__(self):
#       self.name

class BookInstance2(models.Model):
    book = models.ForeignKey('Book',
                             related_name="instances",
                             on_delete=models.CASCADE,
                             null=True)
    pages = models.IntegerField(blank=True)
    isbn10 = models.CharField(max_length=10, blank=True, null=True)
    isbn13 = models.CharField(max_length=13, blank=True, null=True)
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
        ordering = ['due_back']
        verbose_name = 'Book Instance'
        # permissions = (("can_mark_returned", "Set book as returned"),)

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id} ({self.book.title})'
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
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    # RATING_CHOICES = (
    #   (1, 'Poor'),
    #   (2, 'Average'),
    #   (3, 'Good'),
    #   (4, 'Very Good'),
    #   (5, 'Excellent'),
    # )
    # rating = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True)
    class Meta:
        ordering = ('created',)
    def __str__(self):
        return f"Review by {self.user} on {self.book}"