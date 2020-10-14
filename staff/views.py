from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from books.models import BookInstance2
from records2.models import Record
from reservations.models import Reservation
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models.functions import Lower
from django.contrib.admin.views.decorators import staff_member_required

MAX_ALLOWED_LOANS = 6

@staff_member_required
def index(request):
    reservations = Reservation.objects.order_by('reservation_expiry')
    active_records = Record.objects.filter(date_returned__isnull=True)
    context = {
        'reservations': reservations,
        'active_records': active_records,
    }

    return render(request, 'staff/staff_dashboard.html', context)

@staff_member_required
def users(request):
    #users = User.objects.order_by(Lower('username'))
    users = User.objects.order_by('profile__memb_num', 'username')
    keyword = None
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        users_username = users.filter(username__icontains=keyword)
        users_last_name = users.filter(last_name__icontains=keyword)
        if keyword.isnumeric():
            users_memb_num = users.filter(profile__memb_num__icontains=int(keyword))
        else:
            users_memb_num = None
        if users_memb_num:
            users = (users_username | users_last_name | users_memb_num).distinct()
        else:
            users = (users_username | users_last_name).distinct()


    # pagination
    paginator = Paginator(users, 5)
    page = request.GET.get('page')
    paged_users = paginator.get_page(page)

    context = {
        'users': paged_users,
        'query': keyword,
    }
    
    return render(request, 'staff/users.html', context)

@staff_member_required
def user(request, user_id):
    looked_up_user = User.objects.get(id=user_id)
    user_reservations = Reservation.objects.filter(user_id=user_id)
    user_records = Record.objects.filter(user_id=user_id)
    active_user_records = user_records.filter(date_returned__isnull=True)
    active_user_records_count = active_user_records.count()

    # pagination
    paginator = Paginator(user_records, 10)
    page = request.GET.get('page')
    paged_records = paginator.get_page(page)

    context = {
        'looked_up_user': looked_up_user,
        'user_reservations': user_reservations,
        'user_records': paged_records,                  # paged records
        'active_user_records': active_user_records,
        'active_user_records_count': active_user_records_count,
    }
    return render(request, 'staff/user.html', context)

@staff_member_required
def loan_books(request, user_id):

    looked_up_user = User.objects.get(id=user_id)

    # quick check to make sure user is verified
    if not looked_up_user.profile.verified:
        messages.error(request, 'User is not verified')
        return redirect('user', looked_up_user.id)

    # check to see if user has more active loans than is allowed
    active_loans_count = Record.objects.filter(user_id=user_id,date_returned=None).count()
    if active_loans_count >= MAX_ALLOWED_LOANS:
        messages.error(request, 'User has maximum number of active loans allowed (' + str(active_loans_count) + ')')
        return redirect('user', looked_up_user.id)
    loans_possible_num = MAX_ALLOWED_LOANS - active_loans_count

    # change this code to take advantage of can_collect
    user_reservations = Reservation.objects.filter(user_id=user_id)
    reserved_instances = set()
    if user_reservations:

        for reservation in user_reservations:

            book_reservations = Reservation.objects.filter(book=reservation.book).order_by('reservation_date')

            user_placing = 0
            for book_reservation in book_reservations:
                user_placing += 1
                if book_reservation.user_id == user_id:
                    break

            reserved_instances_for_book = BookInstance2.objects.filter(book=reservation.book, status='r')
            number_of_reserved_instances = reserved_instances_for_book.count()

            if user_placing <= number_of_reserved_instances:
                for instance in reserved_instances_for_book:
                    reserved_instances.add(instance)

    available_instances = BookInstance2.objects.filter(status='a')

    context = {
        'available_instances': available_instances,
        'reserved_instances': reserved_instances,
        'looked_up_user': looked_up_user,
        'active_loans_count': active_loans_count,
        'loans_possible_num': loans_possible_num,
    }

    return render(request, 'staff/loan_books.html', context)

@staff_member_required
def execute(request):
    if request.method == 'POST':
        user_id = request.POST['user_id']
        user = User.objects.get(id=user_id)

        # quick check to make sure user is verified
        if not user.profile.verified:
            messages.error(request, 'User is not verified')
            return redirect('user', user.id)

        instances_to_be_loaned_out = set()

        if 'books' not in request.POST:
            messages.error(request, 'Need to select a book, bro')
            return redirect('loan_books', user.id)
        else:
            instance_ids = request.POST.getlist('books')

            for an_id in instance_ids:
                instance = get_object_or_404(BookInstance2, id=an_id)
                instances_to_be_loaned_out.add(instance)

        # so now we have instances

        user_reservations = Reservation.objects.filter(user_id=user_id)

        active_loans_count = Record.objects.filter(user_id=user_id, date_returned__isnull=True).count()

        if len(instances_to_be_loaned_out) + active_loans_count > MAX_ALLOWED_LOANS:
            messages.error(request, 'Too many loans selected')
            return redirect('loan_books', user.id)



        if instances_to_be_loaned_out:
            for an_instance in instances_to_be_loaned_out:
                record = Record.objects.create(
                    user_id=user.id,
                    book_instance_id=an_instance.id,
                    book_title=an_instance.book.title,
                    date_taken_out=date.today()
                )
                an_instance.status = 'o'
                an_instance.due_back = timezone.now() + timezone.timedelta(days=30)
                an_instance.borrower = user
                an_instance.save()

                # remove the reservation for the instance
                if user_reservations:
                    for reservation in user_reservations:
                        if reservation.book.id == an_instance.book.id:
                            reservation.delete()
            messages.success(request, 'The books have been successfully loaned out')
            return redirect('user', user.id)

# @staff_member_required
# def execute(request):
#     # if the submit button has been clicked
#     if request.method == 'POST':

#         user_id = request.POST['user_id']
#         user = User.objects.get(id=user_id)
        
#         # initialise the set
#         instances_to_be_loaned_out = set()

#         # check if option 1 is selected, if so add it to set
#         if request.POST.get('option1') != None:
#             instance_id = request.POST.get('option1')
#             instance = BookInstance2.objects.get(id=instance_id)
#             instances_to_be_loaned_out.add(instance)

#         # ditto with option 2, except there's an added check to see if the option hasn't already been selected
#         if request.POST.get('option2') != None:
#             instance_id = request.POST.get('option2')
#             instance = BookInstance2.objects.get(id=instance_id)
#             if instance in instances_to_be_loaned_out:
#                 messages.error(request, 'You have selected the same instance more than once')
#                 return redirect('loan_books', user.id)
#             else:
#                 instances_to_be_loaned_out.add(instance)

#         # ditto check with option 3
#         if request.POST.get('option3') != None:
#             instance_id = request.POST.get('option3')
#             instance = BookInstance2.objects.get(id=instance_id)
#             if instance in instances_to_be_loaned_out:
#                 messages.error(request, 'You have selected the same instance more than once')
#                 return redirect('loan_books', user.id)
#             else:
#                 instances_to_be_loaned_out.add(instance)

#         # and finally option 4
#         if request.POST.get('option4') != None:
#             instance_id = request.POST.get('option4')
#             instance = BookInstance2.objects.get(id=instance_id)
#             if instance in instances_to_be_loaned_out:
#                 messages.error(request, 'You have selected the same instance more than once')
#                 return redirect('loan_books', user.id)
#             else:
#                 instances_to_be_loaned_out.add(instance)

#         # get the current user's reservations in order to help remove them when an instance is added
#         user_reservations = Reservation.objects.filter(user_id=user.id)

#         if instances_to_be_loaned_out:
#             #add the records
#             for an_instance in instances_to_be_loaned_out:
#                 record = Record(
#                     user_id=user.id,
#                     book_instance_id=an_instance.id,
#                     book_title=an_instance.book.title,
#                     date_taken_out=date.today()
#                 )
#                 record.save()
#                 an_instance.status = 'o'
#                 an_instance.due_back = timezone.now() + timezone.timedelta(days=30) # 30 days from now
#                 an_instance.borrower = user # maybe delete or rethink this
#                 an_instance.save()

#                 # remove the reservation for the instance
#                 if user_reservations:
#                     for reservation in user_reservations:
#                         if reservation.book.id == an_instance.book.id:
#                             reservation.delete()

#             messages.success(request, 'The books have been successfully loaned out')
#             return redirect('user', user.id)
#         else:
#             messages.error(request, 'You have not selected any books')
#             return redirect('loan_books', user.id)

# helper function for returning a book
def return_book(record):
    assert record.date_returned == None
    record.date_returned = timezone.now()
    record.save()

    instance = BookInstance2.objects.get(id=record.book_instance_id)

    # check if there are any waiting reservations
    # if so: change instance status to 'r' and update reservation
    # otherwise change instance status to 'a' and remove borrower
    waiting_reservations = Reservation.objects.filter(book=instance.book, can_collect=False).order_by('reservation_date')
    if waiting_reservations:
        reservation_to_change = waiting_reservations.first()
        reservation_to_change.can_collect = True
        reservation_to_change.reservation_expiry = timezone.now() + timezone.timedelta(days=7)
        reservation_to_change.save()

        instance.status = 'r'
        instance.due_back = None
        instance.save()
    else:
        instance.status = 'a'
        instance.due_back = None
        instance.borrower = None
        instance.save()

@staff_member_required
def return_books(request, user_id):
    looked_up_user = User.objects.get(id=user_id)
    user_records = Record.objects.filter(user_id=user_id)
    active_user_records = user_records.filter(date_returned=None)

    if active_user_records:
        for record in active_user_records:
            return_book(record)
            # record.date_returned = timezone.now()
            # record.save()

            # instance = BookInstance2.objects.get(id=record.book_instance_id)

            # # check if there are any waiting reservations
            # # if so: change instance status to 'r' and update reservation
            # # otherwise change instance status to 'a'
            # waiting_reservations = Reservation.objects.filter(book=instance.book, can_collect=False).order_by('reservation_date')
            # if waiting_reservations:
            #     reservation_to_change = waiting_reservations.first()
            #     reservation_to_change.can_collect = True
            #     reservation_to_change.reservation_expiry = timezone.now() + timezone.timedelta(days=7)
            #     reservation_to_change.save()

            #     instance.status = 'r'
            #     instance.due_back = None
            #     instance.save()
            # else:
            #     instance.status = 'a'
            #     instance.due_back = None
            #     instance.borrower = None
            #     instance.save()

        messages.success(request, 'All books successfully returned')
        return redirect('user', user_id)
    else:
        messages.error(request, 'No active books to return')
        return redirect('user', user_id)

@staff_member_required
def return_single_book(request, record_id):
    record = Record.objects.get(id=record_id)

    if record.date_returned:
        messages.error(request, 'This book has already been returned')
        return redirect('user', record.user_id)
    else:
        return_book(record)
        messages.success(request, f'{record.book_title} successfully returned')
        return redirect('user', record.user_id)

from .forms import StaffUserEditForm, StaffProfileEditForm
@staff_member_required
def staff_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user_form = StaffUserEditForm(instance=user,
                                 data=request.POST)
        profile_form = StaffProfileEditForm(
                                    instance=user.profile,
                                    data=request.POST,
                                    files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'The profile has been updated')
            return redirect('user', user_id)
    else:
        user_form = StaffUserEditForm(instance=user)
        profile_form = StaffProfileEditForm(
                                    instance=user.profile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'staff/edit.html', context)
