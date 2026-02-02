from django import forms
from .models import BookForSale, Author, BookInstance2
from django.db.models import Count
import os
from django.utils.translation import gettext_lazy as _

class CustomImageField(forms.ImageField):
    """
    Using a custom image field to handle scenario of no filename extension having been added.
    We also check the file size of the image doesn't exceed a certain amount.
    """
    def to_python(self, data):
        """
        Custom processing before Django's built-in validation.
        This is called by clean() and runs before the other validation.
        """
        file = super().to_python(data)
        if file:
            # Check and handle missing extension
            ext = os.path.splitext(file.name)[-1]
            if not ext:
                file.name += '.jpg'
        return file

    def clean(self, data, initial=None):
        """
        Custom clean method for the image field
        """
        file = super().clean(data, initial)

        if file:
            # Additional size validation
            max_size_mb = 1
            if file.size > max_size_mb * 1024 * 1024:
                raise forms.ValidationError(
                    _('File size exceeds the maximum limit of %(max_size_mb)sMB.'),
                    params={'max_size_mb': max_size_mb},
                    code='file_size_too_large'
                )
        
        return file


# can't remember what I was thinking with this
class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)

from .models import Review
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        # fields = ('user', 'book', 'title', 'body')
        fields = ['title', 'body', 'rating']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5})
        }

# full text search
# from .choices import category_choices
class SearchForm(forms.Form):
    query = forms.CharField(min_length=3, max_length=60, label='', widget=forms.TextInput(attrs={'placeholder': "Search books"}))
    # category = forms.ChoiceField(choices=category_choices, required=True, label='')

class BookForSaleForm(forms.ModelForm):
    new_author = forms.CharField(
        max_length=255,
        required=False,
        label='Add New Author (if not listed)'
    )

    # Override author so that it's not required
    author = forms.ModelChoiceField(
        # queryset=Author.objects.all(),
        queryset=Author.objects.annotate(book_count=Count('books_for_sale')).filter(book_count__gt=0),  # Filter authors who have books for sale
        required=False,
        label='Select Author'
    )

    # Use CustomImageField for the photo field
    photo = CustomImageField(
        required=False,
        label='Book cover image'
    )

    class Meta:
        model = BookForSale
        fields = ['title', 'author', 'new_author', 'summary', 'isbn', 'sale_category', 'price', 'photo', 'is_sold']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 5}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        author = cleaned_data.get('author')
        new_author = cleaned_data.get('new_author')

        if not author and not new_author:
            raise forms.ValidationError('Please either select an existing author or provide a new author.')

        if author and new_author:
            raise forms.ValidationError('Please select either an existing author or provide a new author, not both.')
        
        return cleaned_data

class AddCopyForm(forms.ModelForm):
    class Meta:
        model = BookInstance2
        fields = [
            "book_type",
            "pages",
            "publisher",
            "isbn10",
            "isbn13",
        ]
    
    def clean_isbn10(self):
        isbn = self.cleaned_data.get("isbn10", "")
        if isbn:
            isbn = isbn.replace("-", "").strip()
        if not isbn:
            return None

        if not isbn.isdigit():
            raise forms.ValidationError("ISBN must contain only digits.")

        if len(isbn) != 10:
            raise forms.ValidationError("ISBN10 must be 10 digits long.")

        return isbn

    def clean_isbn13(self):
        isbn = self.cleaned_data.get("isbn13", "")
        if isbn:
            isbn = isbn.replace("-", "").strip()
        if not isbn:
            return None

        if not isbn.isdigit():
            raise forms.ValidationError("ISBN must contain only digits.")

        if len(isbn) != 13:
            raise forms.ValidationError("ISBN13 must be 13 digits long.")

        return isbn