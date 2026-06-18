from django.db import models
from django.urls import reverse
from django.utils.text import slugify

def upload_location(instance, filename):
    ext = filename.split('.')[-1] if '.' in filename else 'jpg'

    if instance.first_name and instance.last_name:
        first = slugify(instance.first_name, allow_unicode=True)
        last = slugify(instance.last_name, allow_unicode=True)
        first_letter = instance.last_name[:1].upper()
        return f"authors/{first_letter}/{last}_{first}.{ext}"
    
    return f"authors/{filename}"

class Author(models.Model):
    first_name = models.CharField(max_length=100, db_index=True)
    middle_names = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=300,
                            default='',
                            editable=False)
    biography = models.TextField(max_length=1000, blank=True)
    dob = models.DateField(null=True, blank=True)
    dod = models.DateField('Died', null=True, blank=True)
    photo = models.ImageField(upload_to=upload_location, blank=True)
    
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

    def formal(self):
        if self.middle_names:
            return f'{self.last_name}, {self.first_name} {self.middle_names}'
        else:
            return f'{self.last_name}, {self.first_name}'