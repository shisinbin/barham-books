from django import forms
from django.contrib.auth.models import User
# from .models import Profile
from django.utils.translation import ugettext_lazy as _

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
# class ProfileEditForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ('memb_num', 'photo',)
#     # BOOOOOOOMMMMM how'd you like that?
#     # this nifty bit of code disables the membership
#     # number field if it hasn't been entered in yet
#     def __init__(self, *args, **kwargs):
#         super(ProfileEditForm, self).__init__(*args, **kwargs)
#         if self.instance and self.instance.memb_num:
#             self.fields['memb_num'].disabled=True


from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password2"):
            self.add_error("password2", "Passwords do not match")
        return cleaned
