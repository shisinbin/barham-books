from django import forms

class SearchForm(forms.Form):
    query = forms.CharField(min_length=3, max_length=60, label='', widget=forms.TextInput(attrs={'placeholder': "Search books"}))