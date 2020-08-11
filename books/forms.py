from django import forms
class EmailPostForm(forms.Form):
	name = forms.CharField(max_length=25)
	email = forms.EmailField()
	to = forms.EmailField()
	comments = forms.CharField(required=False, widget=forms.Textarea)

from django import forms
from .models import Review
class ReviewForm(forms.ModelForm):
	class Meta:
		model = Review
		fields = ('user', 'book', 'title', 'body')