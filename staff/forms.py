import re
from PIL import Image
from django import forms
from django.contrib.auth.models import User
# from accounts.models import Profile
from django.utils.translation import gettext_lazy as _
from books.models import BookInstance2, Book, BookTags, Series, Category
from authors.models import Author
from PIL import Image

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
        widget=forms.TextInput(attrs={"placeholder": "1234567890123..."})
    )
    title = forms.CharField(
        max_length=255,
        required=False,
        label="Title",
        widget=forms.TextInput(attrs={"placeholder": "moby-dick..."})
    )
    author = forms.CharField(
        max_length=255,
        required=False,
        label="Author",
        widget=forms.TextInput(attrs={"placeholder": "herman melville..."})
    )

    def clean_isbn(self):
        isbn = self.cleaned_data.get("isbn", "").replace("-", "").strip()
        if not isbn:
            return ""
        
        if not isbn.isdigit():
            raise forms.ValidationError("ISBN must contain only digits.")

        if len(isbn) not in (10, 13):
            raise forms.ValidationError("ISBN must be 10 or 13 digits long.")

        return isbn

    def clean_title(self):
        title_raw =  self.cleaned_data["title"].strip()
        if not title_raw:
            return ""

        terms = [word for word in title_raw.split() if len(word) >= 2]

        cleaned_title = " ".join(terms)
        
        if len(cleaned_title) < 3:
            raise forms.ValidationError("Title must be at least 3 characters long.")
        
        return cleaned_title

    def clean_author(self):
        author_raw = self.cleaned_data["author"].strip()
        if not author_raw:
            return ""
        
        terms = [word for word in author_raw.split() if len(word) >= 2]

        cleaned_author = " ".join(terms)
        
        if len(cleaned_author) < 3:
            raise forms.ValidationError("Author must be at least 3 characters long.")
        
        return cleaned_author

    def clean(self):
        cleaned_data = super().clean()

        action = self.data.get("action")
        if action == "manual":
            return cleaned_data

        isbn = cleaned_data.get("isbn")
        title = cleaned_data.get("title")
        author = cleaned_data.get("author")

        if not any([isbn, title, author]):
            raise forms.ValidationError(
                "Enter at least one search field (ISBN, title, or author)."
            )
        return cleaned_data


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
        "rows": 15,
        "placeholder": "Short description or blurb",
        }),
        required=False,
    )

    series_existing = forms.ModelChoiceField(
        queryset=Series.objects.all(),
        required=False,
        label="Select an existing series",
        # empty_label="Select a series",
    )
    series_new = forms.CharField(
        required=False,
        max_length=255,
        label="Or enter a new series name",
        widget=forms.TextInput(),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book_tags'].widget.attrs.update({
            'class': 'js-book-tags',
        })
        self.fields['series_existing'].widget.attrs.update({
            'class': 'js-existing-series',
        })

        self.label_suffix = ""

    def clean_title(self):
        title = self.cleaned_data["title"]
        title = re.sub(r"\s+", " ", title).strip()

        if not title:
            raise forms.ValidationError("Title cannot be empty.")

        if not re.search(r"[A-Za-z0-9]", title):
            raise forms.ValidationError("Title must contain readable characters.")

        return title
    
    def clean_author(self):
        author = self.cleaned_data["author"]
        author = re.sub(r"\s+", " ", author).strip()

        names = author.split()
        if len(names) < 2:
            raise forms.ValidationError("Please enter at least a first and last name.")

        return author

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
        
        # Normalise newlines
        summary = summary.replace('\r\n', '\n').replace('\r', '\n')

        # Remove zero-width and non-breaking spaces
        summary = re.sub(r'[\u200b\u200c\u200d\u00a0]', ' ', summary)

        # Collapse excessive newlines
        summary = re.sub(r'\n{3,}', '\n\n', summary)

        # Collapse excessive spaces
        summary = re.sub(r'[ \t]{2,}', ' ', summary)

        return summary.strip()

"""
--------------- BELOW IS STUFF RELATED TO QUICKLY ADDING BOOK ---------------
"""


def format_book_title(title):
    # Define minor words to leave in lowercase (except the first word)
    minor_words = {'the', 'of', 'with', 'from', 'a', 'an', 'on', 'at', 'for', 'and', 'but', 'in', 'to', 'by', 'or', 'nor', 'as', 'so', 'yet', 'is'}

    words = title.split()

    # Capitalise first word
    # words[0] = words[0].capitalize()

    # Capitalize non-minor words and lowercase minor words
    for i in range(0, len(words)):
        word = words[i]

        # Skip words starting with a number
        if word[0].isdigit():
            continue

        # Skip words that are entirely uppercase
        if word.isupper():
            continue

        # Deal with hyphenated word
        if '-' in word:
            parts = word.split('-')
            words[i] = '-'.join(part.capitalize() for part in parts)
            continue

        # Deal with French d' elision
        if word.lower().startswith("d'"):
            words[i] = f"d'{word[2:].capitalize()}"
            continue

        # Deal with words starting with 'Mc' (could also do 'Mac'?)
        if word.lower().startswith('mc') and len(word) > 2:
            words[i] = f"Mc{word[2:].capitalize()}"
            continue

        # Capitalise the first word of a title regardless
        if i == 0:
            words[0] = word.capitalize()
            continue

        # Capitalise non-minor words and lowercase minor words
        if word.lower() in minor_words:
            words[i] = word.lower()
        else:
            words[i] = word.capitalize()

    # Rejoin the words into a single string
    formatted_title = ' '.join(words)

    def capitalize_after_symbols(title):
        # List of symbols to check for
        symbols = [': ', '& ', '/ ']
        for symbol in symbols:
            if symbol in title:
                initial, rest = title.split(symbol, 1)
                if rest and rest[0].isalpha():
                    # Rebuild the title with character after symbol capitalised
                    title = f"{initial}{symbol}{rest[0].upper()}{rest[1:]}"
        return title
    
    formatted_title = capitalize_after_symbols(formatted_title)

    # Handle titles with a colon
    # if ': ' in formatted_title:
        # initial, rest = formatted_title.split(': ', 1)
        # if rest and rest[0].isalpha():
        #     formatted_title = f"{initial}: {rest[0].upper()}{rest[1:]}"

    # Move starting 'The', 'A', or 'An' to the end
    if formatted_title.lower().startswith(('the ', 'a ', 'an ')):
        first_word, rest_of_title = formatted_title.split(' ', 1)
        formatted_title = f"{rest_of_title}, {first_word}"

    return formatted_title

def format_author_name(author_name):
    """
    Formats an author's name.
    For names like 'J.K. Rowling' or 'J R R Tolkien', combines initials into the first name.
    For regular names like 'John Adam George Smith', processes first, middle, and last names conventionally.
    """
    # Remove periods and normalize whitespace
    author_name = re.sub(r'\.', ' ', author_name).strip()
    names = author_name.split()
    
    if len(names) < 2:
        raise ValueError("Need to enter a first and last name for the author.")

    # Case 1: Initials-based names (e.g., "J R R Tolkien" -> "JRR Tolkien")
    if all(len(name) == 1 for name in names[:-1]):  # Check if all but the last are single characters
        first_name = ''.join(n.upper() for n in names[:-1])  # Combine all initials into the first name
        middle_name = ''  # No middle name for initials-based names
        if '-' in names[-1]:
            partials = names[-1].split('-')
            last_name = '-'.join(p.capitalize() for p in partials)
        else:
            last_name = names[-1].capitalize()
    else:
        # Case 2: Regular names (e.g., "John Adam George Alexander Smith")
        first_name = names[0].capitalize()
        middle_name = ' '.join(names[1:-1]).title() if len(names) > 2 else ''
        if '-' in names[-1]:
            partials = names[-1].split('-')
            last_name = '-'.join(p.capitalize() for p in partials)
        else:
            last_name = names[-1].capitalize()

    return first_name, middle_name, last_name

def process_author_from_form(cleaned_data):
    title = cleaned_data.get('title')
    if not title:
        raise ValueError("Title is required before author validation")

    if cleaned_data.get('author_select'):
        author = cleaned_data['author_select']
        if Book.objects.filter(title__iexact=title, author=author).exists():
            raise ValueError("Book already in database")
        return author

    if cleaned_data.get('author'):
        first, middle, last = format_author_name(cleaned_data['author'])
        author = Author.objects.filter(
            first_name__iexact=first,
            last_name__iexact=last
        ).first()

        if author and Book.objects.filter(title__iexact=title, author=author).exists():
            raise ValueError("Book already in database")

        return author or Author(
            first_name=first,
            middle_names=middle,
            last_name=last
        )

    raise ValueError("Please select or enter an author")

def is_valid_image(file):
    try:
        image = Image.open(file)
        image.verify()
        return True
    except Exception:
        return False

class AddBookQuickForm(forms.Form):
    title = forms.CharField(max_length=255, label="Book title")
    
    author_select = forms.ModelChoiceField(
        queryset=Author.objects.all(),
        required=False,
        label="Select an existing author"
    )
    author = forms.CharField(required=False, label="Or enter new author")

    category = forms.ModelChoiceField(queryset=Category.objects.all())
    book_type = forms.ChoiceField(choices=[
        ('p', 'Paperback'),
        ('h', 'Hardcover'),
        ('o', 'Oversized'),
    ])

    series_select = forms.ModelChoiceField(
        queryset=Series.objects.all(),
        required=False, 
        label="Select series (if applicable)"
    )
    series = forms.CharField(required=False, label="Or enter new series")
    series_num = forms.IntegerField(required=False, min_value=1, label="Series #")

    summary = forms.CharField(
        widget=forms.Textarea(attrs={
        "rows": 15,
        }),
        required=False,
        max_length=2000,
        label="Book summary (optional)"
    )

    photo = forms.ImageField(required=False,label="Book cover image (optional)")

    isbn10 = forms.CharField(required=False, label="ISBN10")
    isbn13 = forms.CharField(required=False, label="ISBN13")

    pages = forms.IntegerField(required=False, min_value=1)
    publisher = forms.CharField(required=False)
    year = forms.IntegerField(required=False, min_value=1000, max_value=2100, label="Publication Year")

    is_featured = forms.BooleanField(required=False, label="Check box to make book featured")

    book_tags = forms.ModelMultipleChoiceField(
        queryset=BookTags.objects.filter(band=1),
        required=False,
        label="Book Tags (optional)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['book_tags'].widget.attrs.update({
            'class': 'js-book-tags',
        })
        self.fields['series_select'].widget.attrs.update({
            'class': 'js-existing-series',
        })
        self.fields['author_select'].widget.attrs.update({
            'class': 'js-existing-author',
        })

        self.label_suffix = ""

    def clean_title(self):
        title = re.sub(r"\s+", " ", self.cleaned_data["title"]).strip()

        if not title:
            raise forms.ValidationError("Title cannot be empty.")

        if not re.search(r"[A-Za-z0-9]", title):
            raise forms.ValidationError("Title must contain readable characters.")

        return title

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if not photo:
            return photo

        max_size_mb = 1
        if photo.size > max_size_mb * 1024 * 1024:
            raise forms.ValidationError(
                f"Image file size exceeds {max_size_mb}MB."
            )

        if '.' not in photo.name:
            photo.name += '.jpg'

        if not is_valid_image(photo):
            raise forms.ValidationError("Uploaded file is not a valid image.")

        return photo

    def clean(self):
        cleaned = super().clean()

        if self.errors:
            return cleaned

        # Author validation
        try:
            cleaned['author_obj'] = process_author_from_form(cleaned)
        except ValueError as e:
            raise forms.ValidationError(str(e))

        # Series handling
        series = cleaned.get('series_select')

        if not series and cleaned.get('series'):
            series, _ = Series.objects.get_or_create(
                name=cleaned['series']
            )
        
        cleaned['series_obj'] = series

        if series and not cleaned.get('series_num'):
            cleaned['series_num'] = 99

        return cleaned

    def clean_isbn10(self):
        isbn = self.cleaned_data.get("isbn10", "").replace("-", "").strip()
        if not isbn:
            return ""
        
        if not isbn.isdigit():
            raise forms.ValidationError("ISBN must contain only digits.")

        if len(isbn) != 10:
            raise forms.ValidationError("ISBN10 must be 10 digits long.")

        return isbn

    def clean_isbn13(self):
        isbn = self.cleaned_data.get("isbn13", "").replace("-", "").strip()
        if not isbn:
            return ""
        
        if not isbn.isdigit():
            raise forms.ValidationError("ISBN must contain only digits.")

        if len(isbn) != 13:
            raise forms.ValidationError("ISBN13 must be 13 digits long.")

        return isbn