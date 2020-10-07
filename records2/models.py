from django.db import models
from django.utils import timezone
from books.models import BookInstance2
from django.shortcuts import redirect
from django.contrib.auth.models import User
from datetime import date

class Record(models.Model):
    user_id = models.IntegerField(db_index=True)
    book_instance_id = models.IntegerField()
    book_title = models.CharField(max_length=200, default='title', blank=True)
    date_taken_out = models.DateField(default=timezone.now)
    date_returned = models.DateField(blank=True, null=True)
    extended = models.BooleanField(default=False)
    class Meta:
        ordering = ('-date_returned',)
    def __str__(self):
        return f"{self.book_title}: {self.user_id}"
    def get_due_back_date(self):
        if self.date_returned:
            return ''
        else:
            if self.date_taken_out:
                if self.extended:
                    return self.date_taken_out + timezone.timedelta(days=60)
                else:
                    return self.date_taken_out + timezone.timedelta(days=30)
            else:
                return ''
    def get_book_link(self):
        try:
            book = BookInstance2.objects.get(id=self.book_instance_id).book
            return book.get_absolute_url()
        except:
            return '#'
    def get_username(self):
        try:
            user = User.objects.get(id=self.user_id)
            return user.username
        except:
            return ''

    @property
    def is_overdue(self):
        if self.get_due_back_date() != '' and date.today() > self.get_due_back_date():
            return True
        return False