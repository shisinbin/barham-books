from django import forms
from .models import BookForSale, Author
from django.db.models import Count

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
        fields = ('user', 'book', 'title', 'body')

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