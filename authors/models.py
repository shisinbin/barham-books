from django.db import models
import os
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

def upload_location(instance, filename):
    ext = filename.split('.')[-1]
    if instance.first_name and instance.last_name:
        new_filename = f"authors/{instance.last_name[:1].upper()}/{instance.last_name.lower()}_{instance.first_name.lower()}.{ext}"
    else:
        new_filename = filename
    return os.path.join(settings.MEDIA_ROOT, new_filename)


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    middle_names = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=300,
                            default='',
                            editable=False)
    biography = models.TextField(max_length=1000, blank=True)
    dob = models.DateField(null=True, blank=True)
    dod = models.DateField('Died', null=True, blank=True)
    photo = models.ImageField(upload_to=upload_location, blank=True)
    is_featured = models.BooleanField(default=False)
    class Meta:
        ordering = ['last_name', 'first_name']
    def __str__(self):
        if self.middle_names:
            return f'{self.first_name} {self.middle_names} {self.last_name}'
        else:
            return f'{self.first_name} {self.last_name}'
    def get_absolute_url(self):
        return reverse('author',
                       args=[str(self.id),
                             self.slug])
    def save(self, *args, **kwargs):
        value = self.__str__()
        self.slug = slugify(value, allow_unicode=True)
        super().save(*args, **kwargs)