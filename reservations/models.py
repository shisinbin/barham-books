from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from books.models import Book
from datetime import date

class Reservation(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user_id = models.IntegerField(db_index=True)
    # user_email = models.CharField(max_length=100)
    reservation_date = models.DateTimeField(default=timezone.now)
    can_collect = models.BooleanField(default=False)
    reservation_expiry = models.DateTimeField(blank=True, null=True)
    class Meta:
        ordering = ('-reservation_date',)
    def __str__(self):
        return self.book.title
    def get_username(self):
        try:
            user = User.objects.get(id=self.user_id)
            return user.username
        except:
            return ''
    def expired(self):
        if self.reservation_expiry and date.today() > self.reservation_expiry.date():
            return True
        else:
            return False