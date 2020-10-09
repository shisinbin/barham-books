from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import date
from django.contrib import messages
from records2.models import Record
from books.models import BookInstance2, Book
from .models import Reservation
from django.core.mail import send_mail

MAX_ALLOWED_RESERVATIONS = 6

def reserve(request):
	if request.method == 'POST':
		user_id = request.POST['user_id'] # could instead use request.user
		book = Book.objects.get(id=request.POST['book_id'])

		user_reservations = Reservation.objects.filter(user_id=user_id)

		# check to see user hasn't made more reservations than allowed
		if user_reservations.count() >= MAX_ALLOWED_RESERVATIONS:
			messages.error(request, 'You have the maximum number of reservations and cannot make any more')
			return redirect('book', book.id, book.slug)
		else:
			# check to see if user has book on loan
			record_queryset = Record.objects.filter(user_id=user_id, book_title=book.title, date_returned=None)
			if record_queryset:
				messages.error(request, 'You already have this book on loan')
				return redirect('book', book.id, book.slug)
			else:
				# check to see if user has an active reservation for the book
				if user_reservations.filter(book=book):
					messages.error(request, 'You have already reserved this book')
					return redirect('book', book.id, book.slug)
				else:
					# change status on one of the book instances
					instances = book.instances.all()
					did_change_status = False
					for instance in instances:
						if instance.status == 'a':
							instance.status = 'r'
							instance.save()
							did_change_status = True
							break

					if did_change_status:
						reservation = Reservation(book=book, user_id=user_id, reservation_date=timezone.now(), can_collect=True, reservation_expiry=timezone.now()+timezone.timedelta(days=7))
						reservation.save()
						# send_mail(
						# 	f"Reservation: {reservation.book.title}",
						# 	f"Hi {request.user.username}.\n\nYour reservation for the book titled {reservation.book.title}, is now active. A copy of the book is being held in the library and can be collected.\nNote that the reservation will expire in one week's time.\n\nRegards,\nBarham Library",
						# 	'enthuzimuzzy00@gmail.com',
						# 	[request.user.email,],
						# 	fail_silently=False
						# 	)
					else:
						reservation = Reservation(book=book, user_id=user_id, reservation_date=timezone.now())
						reservation.save()

					messages.success(request, 'You have now reserved this book')
					return redirect('book', book.id, book.slug) # or /book/+book.id if id was a string