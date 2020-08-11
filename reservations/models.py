from django.db import models
from django.utils import timezone

from books.models import Book

class Reservation(models.Model):
	book = models.ForeignKey(Book, on_delete=models.CASCADE)
	user_id = models.IntegerField()
	# user_email = models.CharField(max_length=100)
	reservation_date = models.DateTimeField(default=timezone.now)
	can_collect = models.BooleanField(default=False)
	reservation_expiry = models.DateTimeField(blank=True, null=True)
	def __str__(self):
		return self.book.title