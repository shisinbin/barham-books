import re
from PIL import Image
from django import forms
from django.contrib.auth.models import User
# from accounts.models import Profile
from django.utils.translation import ugettext_lazy as _
from books.models import BookInstance2, Book, BookTags, Series, Category
from .helpers import format_book_title, format_author_name

LANGUAGE_CHOICES = (
        ('English', 'English'),
        ('Hindi', 'Hindi'),
        ('Russian', 'Russian'),
        ('Spanish', 'Spanish'),
    )

class StaffUserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email',)
# class StaffProfileEditForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ('memb_num', 'photo', 'verified',)

class AddBookCopy(forms.ModelForm):
    class Meta:
        model = BookInstance2
        fields = ('book_type', 'pages', 'publisher', 'isbn10', 'isbn13',)

class StaffBookLookupForm(forms.Form):
    isbn = forms.CharField(
        max_length=20,
        required=False,
        label="ISBN",
        widget=forms.TextInput(attrs={"placeholder": "1234567890..."})
    )
    title = forms.CharField(
        max_length=255,
        required=False,
        label="Title",
        widget=forms.TextInput(attrs={"placeholder": "george's marvellous medicine..."})
    )
    author = forms.CharField(
        max_length=255,
        required=False,
        label="Author",
        widget=forms.TextInput(attrs={"placeholder": "roald dahl..."})
    )

    def clean(self):
        cleaned = super().clean()
        if not any(cleaned.values()):
            raise forms.ValidationError(
                "Enter at least one search field (ISBN, title, or author)."
            )
        return cleaned


class BookDraftForm(forms.Form):
    photo = forms.ImageField(
        required=False,
        help_text="JPEG or PNG, max 1MB",
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
    )

    title = forms.CharField(max_length=255, label="Book title")
    author = forms.CharField(max_length=255, label="Author name")

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        # initial=Category.objects.get(code="GEN"),
    )
    book_type = forms.ChoiceField(choices=BookInstance2.BOOK_TYPE_CHOICES)

    book_tags = forms.ModelMultipleChoiceField(
        queryset=BookTags.objects.all(),
        required=False,
    )

    summary = forms.CharField(
        widget=forms.Textarea(attrs={
        "rows": 5,
        "placeholder": "Short description or blurb",
        }),
        required=False,
    )

    series_existing = forms.ModelChoiceField(
        queryset=Series.objects.all(),
        required=False,
        label="Select an existing series",
        # empty_label="Select a series",
        empty_label="",
    )
    series_new = forms.CharField(
        required=False,
        max_length=255,
        label="Or create a new series"
        )
    series_num = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=99,
        label="Series number"
    )

    isbn = forms.CharField(
        required=False,
        max_length=20,
        label="ISBN",
        help_text="ISBN-10 or ISBN-13",
    )

    language = forms.CharField(max_length=50)
    pages = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=99999,
        label="Number of pages"
    )
    publisher = forms.CharField(required=False, max_length=100)
    year = forms.IntegerField(
        required=False,
        min_value=1000,
        max_value=2100,
        label="Publication year"
    )
    is_featured = forms.BooleanField(
        required=False,
        label="Add to Featured books?"
    )

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Title cannot be empty.")

        return format_book_title(title)
    
    def clean_author(self):
        author = self.cleaned_data["author"].strip()
        if not author:
            raise forms.ValidationError("Please enter an author name.")

        return format_author_name(author)

    def clean_isbn(self):
        isbn = self.cleaned_data.get("isbn", "").replace("-", "").strip()
        if not isbn:
            return ""
        
        if not isbn.isdigit():
            raise forms.ValidationError("ISBN must contain only digits.")

        if len(isbn) not in (10, 13):
            raise forms.ValidationError("ISBN must be 10 or 13 digits long.")

        return isbn

    def clean(self):
        cleaned = super().clean()

        series_existing = cleaned.get("series_existing")
        series_new = cleaned.get("series_new")
        series_num = cleaned.get("series_num")

        if series_existing and series_new:
            raise forms.ValidationError(
                "Choose an existing series or enter a new one, not both."
            )
        
        if (series_existing or series_new) and not series_num:
            cleaned["series_num"] = 99
        
        return cleaned

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")

        if not photo:
            return photo
        
        max_size_mb = 1
        max_size_bytes = max_size_mb * 1024 * 1024

        # Size check
        if photo.size > max_size_bytes:
            raise forms.ValidationError(
                f"Image file size exceeds the maximum limit of {max_size_mb}MB."
            )
        
        # Ensure image can actually be opened
        try:
            img = Image.open(photo)
            img.verify()
        except Exception:
            raise forms.ValidationError("The uploaded file is not a valid image.")
        finally:
            photo.seek(0)
        
        # Normalise extension (non-blocking)
        if "." not in photo.name:
            photo.name += ".jpg"
        
        return photo
    
    def clean_summary(self):
        summary = self.cleaned_data.get("summary", "")
        if not summary:
            return summary
        
        # Light normalisation
        summary = summary.strip()
        summary = re.sub(r"\n{3,}", "\n\n", summary)

        return summary
