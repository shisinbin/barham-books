from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.models import User
from books.models import BookInstance2, Review
from reservations.models import Reservation
from records2.models import Record
from django.utils import timezone
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

def register(request):
	if request.method == 'POST':
		# Get form values
		first_name = request.POST['first_name']
		last_name = request.POST['last_name']
		username = request.POST['username']
		email = request.POST['email']
		password = request.POST['password']
		password2 = request.POST['password2']

		# Check if passwords match
		if password == password2:
			# Check username
			if User.objects.filter(username=username).exists():
				messages.error(request, 'Username is taken')
				return redirect('register')
			else:
				# Check email
				if User.objects.filter(email=email).exists():
					messages.error(request, 'That email is being used')
					return redirect('register')
				else:
					# Looks good
					user = User.objects.create_user(
						username=username,
						password=password,
						first_name=first_name,
						last_name=last_name,
						email=email)
					user.save()
					messages.success(request, 'You are now registered and can log in')
					return redirect('login')
		else:
			messages.error(request, 'Passwords do not match')
			return redirect('register')
	else:
		return render(request, 'accounts/register.html')

def login(request):
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		
		user = auth.authenticate(username=username, password=password)
		
		if user is not None:
			auth.login(request, user)
			messages.success(request, 'You are now logged in')
			return redirect('dashboard')
		else:
			messages.error(request, 'Invalid credentials')
			return redirect('login')
	else:
		return render(request, 'accounts/login.html')

def logout(request):
	if request.method == 'POST':
		auth.logout(request)
		messages.success(request, 'You are now logged out')
		return redirect('index')

from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
	user_reservations = Reservation.objects.filter(user_id=request.user.id)

	user_records = Record.objects.filter(user_id=request.user.id)
	# are there active loans not returned?
	if user_records.filter(date_returned__isnull=True):
		active = True
	else:
		active = False
	# are there records user can extend?
	if user_records.filter(date_returned__isnull=True, extended=False):
		can_extend = True
	else:
		can_extend = False
	# slice the most recent 5
	user_records = user_records[:5]

	books_liked = request.user.books_liked.all()

	context = {
		'user_reservations': user_reservations,
		'user_records': user_records,
		'books_liked': books_liked,
		'active': active,
		'can_extend': can_extend,
	}
	return render(request, 'accounts/dashboard.html', context)

@login_required
def view_records(request):
	user_records = Record.objects.filter(user_id=request.user.id)

	if user_records.filter(date_returned__isnull=True):
		active = True
	else:
		active = False

	if user_records.filter(date_returned__isnull=True, extended=False):
		can_extend = True
	else:
		can_extend = False

	total_num = None
	if user_records:
		total_num = len(user_records)
	else:
		return redirect('dashboard')
	# pagination
	paginator = Paginator(user_records, 10)
	page = request.GET.get('page')
	paged_records = paginator.get_page(page)

	context = {
		'user_records': paged_records,
		'total_num': total_num,
		'active': active,
		'can_extend': can_extend,
	}

	return render(request, 'accounts/records.html', context)

@login_required
def delete_reservation(request):
	if request.method == 'POST':
		reservation_id = request.POST.get('del_reservation')
		if reservation_id:
			reservation = Reservation.objects.get(id=reservation_id)

			# if the reservation was directly reserving a book title
			if reservation.can_collect:

				waiting_reservations = Reservation.objects.filter(book=reservation.book, can_collect=False)

				# if there are other reservations who aren't able to collect yet
				if waiting_reservations:
					# get the first waiting reservation and update
					reservation_to_change = waiting_reservations.first()
					reservation_to_change.can_collect = True
					reservation_to_change.reservation_expiry = timezone.now() + timezone.timedelta(days=7)
					reservation_to_change.save()
					# and send email innit
				else:
					# change the status of any ONE of book's RESERVED instances
					instance = BookInstance2.objects.filter(book=reservation.book, status='r').first()
					instance.status = 'a'
					instance.save()

			reservation.delete()
			messages.success(request, 'Reservation successfully deleted')
			if request.user.is_staff:
				return redirect('staff')
			else:
				return redirect('dashboard')
		else:
			messages.error(request, 'You did not select a reservation to delete')
			if request.user.is_staff:
				return redirect('staff')
			else:
				return redirect('dashboard')

@login_required
def extend_all_loans(request):
	if request.method == 'POST':
		active_records = Record.objects.filter(user_id=request.user.id, date_returned__isnull=True)
		if active_records:
			# a count for showing how many of a user's records have been extended
			count = 0
			for record in active_records:
				# if the loan hasn't been extended before
				if not record.extended:
					try:
						bk_instance = BookInstance2.objects.get(id=record.book_instance_id)
					except:
						messages.error(request, 'Error: book instance not found. Email for help')
						return redirect('dashboard')
					bk_instance.due_back += timezone.timedelta(days=30)
					bk_instance.save()
					count += 1
					record.extended = True
					record.save()
			if count == 0:
				messages.error(request, 'You have already renewed all active loans once before')
				return redirect('dashboard')
			elif count == len(active_records):
				messages.success(request, 'You have renewed all active loans')
				return redirect('dashboard')
			else:
				messages.success(request, 'You have renewed ' + str(count) + ' of your active loans')
				return redirect('dashboard')

		else:
			messages.error(request, 'You do not have any active loans to renew')
			return redirect('dashboard')