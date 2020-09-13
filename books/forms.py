from django import forms

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
class SearchForm(forms.Form):
    query = forms.CharField(min_length=4, max_length=60, label='', widget=forms.TextInput(attrs={'placeholder': "e.g. dragon tattoo millenium larsson"}))