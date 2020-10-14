from django import forms
from django.contrib.auth.models import User
from accounts.models import Profile
from django.utils.translation import ugettext_lazy as _

class StaffUserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email',)
class StaffProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('memb_num', 'photo', 'verified',)