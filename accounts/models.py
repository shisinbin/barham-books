# from django.db import models
# from django.conf import settings
# from django.core.validators import MaxValueValidator, MinValueValidator


def upload_location(instance, filename):
    """
    LEGACY FUNCTION - DO NOT REMOVE.
    Required for historical migrations that reference this symbol.
    """
    ext = filename.split('.')[-1]
    if instance.user.username:
        new_filename = f"users/{instance.user.username[:1].upper()}/{instance.user.username}.{ext}"
    else:
        new_filename = f"users/{filename}"
    return new_filename

# class Profile(models.Model):
#     user = models.OneToOneField(settings.AUTH_USER_MODEL,
#                                 on_delete=models.CASCADE,
#                                 related_name="profile")
#     memb_num = models.PositiveIntegerField(
#         blank=True,
#         null=True,
#         unique=True,
#         verbose_name="membership number",
#         validators=[MinValueValidator(1), MaxValueValidator(999)])
#     photo = models.ImageField(upload_to=upload_location, blank=True, verbose_name='profile photo')
#     verified = models.BooleanField(default=False)
#     def __str__(self):
#         return f'Profile for user {self.user.username}'