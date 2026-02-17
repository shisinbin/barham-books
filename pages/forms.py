from django import forms
from turnstile.fields import TurnstileField

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)

    # Bots autofill hidden fields. Humans never see it.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    # Cloudfare Turnstile
    turnstile = TurnstileField()

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('Bot detected.')
        return ""