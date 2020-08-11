from django.db import models
from django.utils import timezone
from books.models import BookInstance2

class Record(models.Model):
	user_id = models.IntegerField()
	book_instance_id = models.IntegerField()
	book_title = models.CharField(max_length=200, default='title', blank=True)
	date_taken_out = models.DateField(default=timezone.now)
	date_returned = models.DateField(blank=True, null=True)
	class Meta:
		ordering = ('-date_returned',)
	def __str__(self):
		return f"{self.book_title}: {self.user_id}"