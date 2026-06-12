from turnstile.fields import TurnstileField

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    turnstile = TurnstileField()

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean_email(self):
        email = self.cleaned_data["email", ""].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password2"):
            self.add_error("password2", "Passwords do not match")
        return cleaned

class PasswordResetTurnstileForm(PasswordResetForm):
    turnstile = TurnstileField()