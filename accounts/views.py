from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.models import User
from books.models import BookInstance2
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
	user_reservations = Reservation.objects.filter(user_id=request.user.id).order_by('-reservation_date')
	user_records = Record.objects.filter(user_id=request.user.id).order_by('-date_returned')

	# pagination
	paginator = Paginator(user_records, 8)
	page = request.GET.get('page')
	paged_records = paginator.get_page(page)

	context = {
		'user_reservations': user_reservations,
		'user_records': paged_records,
	}
	return render(request, 'accounts/dashboard.html', context)

# maybe add a login_required decorator here too
def delete_reservation(request):
	if request.method == 'POST':
		reservation_id = request.POST.get('del_reservation')
		if reservation_id:
			reservation = Reservation.objects.get(id=reservation_id)

			# if the reservation was directly reserving a book title
			if reservation.can_collect:

				waiting_reservations = Reservation.objects.filter(book=reservation.book, can_collect=False).order_by('reservation_date')

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
			return redirect('dashboard')
		else:
			messages.error(request, 'You did not select a reservation to delete')
			return redirect('dashboard')



from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance2
    template_name ='accounts/borrowed.html'
    paginate_by = 10
    
    def get_queryset(self):
        return BookInstance2.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')