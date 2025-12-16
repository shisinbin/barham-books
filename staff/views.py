from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from books.models import BookInstance2, Book
from authors.models import Author
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
    users = User.objects.order_by('profile__memb_num', Lower('username'))
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
    paginator = Paginator(users, 10)
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

@staff_member_required
def del_copy(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if BookInstance2.objects.filter(book=book):
        # crappy way of deleting a copy
        BookInstance2.objects.filter(book=book).order_by('-pk')[0].delete()
        messages.success(request,'A copy was successfully deleted')
    else:
        messages.error(request, 'The book already has no copies')
    return redirect(book)

from .forms import AddBookCopy
@staff_member_required
def add_copy(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if book.instances.count() >= 3:
        messages.error(request, 'Max number of copies reached')
        return redirect(book)
    if request.method=='POST':
        form_data = AddBookCopy(request.POST)
        if form_data.is_valid():
            instance = form_data.save(commit=False)
            instance.book = book
            instance.save()
            messages.success(request, 'A copy has been added')
        else:
            messages.error(request,'Something went wrong')
        return redirect(book)

def capitalize_first_char(s):
    return s[0].upper() + s[1:]

@staff_member_required
def amend_author(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    current_author = get_object_or_404(Author, id=book.author.id)

    if request.method == 'POST':
        full_name = request.POST.get('author', '').strip()

        if not full_name:
            messages.error(request, 'No author entered')
            return redirect(book)
        
        names = full_name.split()
        if len(names) < 2:
            messages.error(request, 'Both a first and last name are required')
            return redirect(book)
        
        first_name = capitalize_first_char(names.pop(0))
        last_name = capitalize_first_char(names.pop())

        middle_names = ''
        if names:
            capitalized_middle_names = [capitalize_first_char(name) for name in names]
            middle_names = ' '.join(capitalized_middle_names)


        # Try to see if new author is already in DB, if not then create new one
        try:
            new_author = Author.objects.get(first_name__iexact=first_name, last_name__iexact=last_name)

            # Check to see if author found in DB is not the same as book's current author
            if current_author == new_author:
                messages.info(request, 'Author remains unchanged')
                return redirect(book)
        except Author.DoesNotExist:
            new_author = Author.objects.create(first_name=first_name, middle_names=middle_names, last_name=last_name)

        book.author = new_author
        book.save()

        # Delete the old author if they have no associated books
        if current_author.books.count() == 0:
            current_author.delete()
            messages.success(request, 'Author has been changed and previous author deleted')
        else:
            messages.success(request, 'Author has been changed')
        
        return redirect(book)

import requests

# def fetch_book_cover(isbn):
#     """
#     Fetches the cover image for a book using its ISBN from the Open Library API.

#     Args:
#         isbn (str): The ISBN of the book.

#     Returns:
#         bytes: The binary content of the book cover image if found, None otherwise.
#     """
#     url = f'https://openlibrary.org/search.json?isbn={isbn}'

#     try:
#         print(f'Fetching book cover for ISBN: {isbn}')
#         response = requests.get(url)
#         response.raise_for_status()
#         data = response.json()

#         book_info = data.get('docs', [])
#         if book_info:
#             first_book = book_info[0]
#             cover_edition_key = first_book.get('cover_edition_key')
#             cover_i = first_book.get('cover_i')

#             image_url = None
#             if cover_edition_key:
#                 image_url = f'https://covers.openlibrary.org/b/olid/{cover_edition_key}-L.jpg'
#             elif cover_i:
#                 image_url = f'https://covers.openlibrary.org/b/id/{cover_i}-L.jpg'
            
#             if image_url:
#                 print(f"Downloading image from URL: {image_url}")
#                 response = requests.get(image_url, stream=True)
#                 response.raise_for_status()
#                 print(f'Size of image is: {len(response.content)}')
#                 return response.content
#             else:
#                 print("No image URL found.")
#                 return None
#         else:
#             print("No book information found.")
#             return None
#     except Exception as e:
#         print(f"Error fetching book data: {e}")
#         return None

def fetch_book_cover(isbn, size='L'):
    """
    Fetches the cover image for a book using its ISBN from the Open Library Covers API.

    Args:
        isbn (str): The ISBN of the book.
        size (str): One of 'S', 'M', 'L'

    Returns:
        bytes | None: Image content if found, otherwise None.
    """
    url = f'https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg?default=false'

    try:
        print(f'Fetching cover from: {url}')
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            print(f'No cover found for ISBN.')
            return None

        response.raise_for_status()
        return response.content
    
    except requests.RequestException as e:
        print(f'Error fetching cover image: {e}')
        return None

import os
from django.conf import settings
@staff_member_required
def lookup_book_cover (request, book_id):
    """
    Looks up and displays a temporary cover image for a book based on its ISBN.

    If the book already has a cover image, it redirects with an error message.
    If the book has no associated ISBNs, it redirects with a warning message.
    If the fetched image exceeds the maximum file size (1MB), it redirects with an error message.
    Otherwise, it saves the fetched image temporarily and renders a page with the book and temporary image.

    Args:
        request (HttpRequest): The HTTP request object.
        book_id (int): The ID of the book for which to lookup the cover image.

    Returns:
        HttpResponse: A rendered HTML page displaying the book and temporary cover image.
    """

    # Get the book object
    book = get_object_or_404(Book, id=book_id)

    # Check if the book already has a cover image
    if book.photo:
        messages.error(request, 'Book already has a cover image.')
        return redirect(book)
    
    # Create a list of ISBNs from book
    isbn_list = []
    for instance in book.instances.all():
        if instance.isbn10:
            isbn_list.append(instance.isbn10)
        if instance.isbn13:
            isbn_list.append(instance.isbn13)
    
    if not isbn_list:
        messages.warning(request, 'Book does not have an associated ISBN. Please add one.')
        return redirect(book)
    
    # Use ISBN's to find first valid cover image
    image_content = None
    for isbn in isbn_list:
        image_content = fetch_book_cover(isbn)
        if image_content != None:
            break
    
    # Check to see that an image was fetched from API
    if image_content == None:
        messages.error(request, 'No cover image found on Open Library for this ISBN.')
        return redirect(book)
    
    # Check to see that image does not exceed maximum filesize
    image_size = len(image_content)
    max_image_size = 1024 * 1024 # 1MB
    if image_size > max_image_size:
        messages.error(request, 'Image found, but filesize exceeds maximum. Sorry :(')
        return redirect(book)
    
    print("Image content retrieved successfully.")

    # Add a temporary folder if there is none
    temp_folder = os.path.join(settings.MEDIA_ROOT, 'temp')
    if not os.path.exists(temp_folder):
        print('Temp folder created in Media directory to hold temporary cover image')
        os.makedirs(temp_folder)
    
    # Write the image to temporary folder
    temp_image_path = os.path.join(settings.MEDIA_ROOT, 'temp', 'cover_image.jpg')
    with open(temp_image_path, 'wb') as temp_image_file:
        temp_image_file.write(image_content)

    # For this temporary image, get the url
    temp_image_url = os.path.join(settings.MEDIA_URL, 'temp', 'cover_image.jpg')

    context = {
        'book': book,
        'temp_image_url': temp_image_url
    }

    return render(request, 'staff/lookup_book_cover.html', context)


@staff_member_required
def associate_book_cover(request, book_id):
    """
    Associates a temporary cover image with a book and deletes the temporary image file.

    If the HTTP request method is POST:
        - Checks if the temporary image file exists.
        - If it exists, sets the book's photo field to the image file and deletes the temporary file.
        - Redirects the user to the book detail page with a success message.
        - If the temporary image file doesn't exist, shows an error message.

    If the HTTP request method is not POST, redirects the user to the book page.

    Args:
        request (HttpRequest): The HTTP request object.
        book_id (int): The ID of the book to associate the cover image with.

    Returns:
        HttpResponse: Redirects to the book detail page or book page based on the request method.
    """
    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        # Set the book.photo field to the URL of the temporary image
        temp_image_path = os.path.join(settings.MEDIA_ROOT, 'temp', 'cover_image.jpg')

        if os.path.exists(temp_image_path):
            # Open the temporary image file and assign it to book.photo
            with open(temp_image_path, 'rb') as temp_image_file:
                book.photo.save('cover_image.jpg', temp_image_file, save=True)
            
            # Delete the temporary image file from the server
            os.remove(temp_image_path)

            # Redirect the user to the book detail page
            messages.success(request, 'Image successfully associated to book!')
            return redirect(book)
        else:
            # If the temporary image file doesn't exist, show message
            messages.error(request, 'Temporary image file not found!')
            return redirect(book)

    # If the request method is not POST, redirect the user to the book page
    return redirect(book)

# This is for a future implementation
# @staff_member_required
# def search_books(request):
#     if request.method == 'GET':
#         title = request.GET.get('title', '')
#         author = request.GET.get('author', '')
#         isbn = request.GET.get('isbn', '')

#         # Perform the search based on the provided criteria
#         search_results = []
#         if title or author or isbn:
#             api_url = 'https://openlibrary.org/search.json'
#             params = {
#                 # 'title': title,
#                 # 'author': author,
#                 # 'isbn': isbn,
#                 'q': title,
#             }

#             response = requests.get(api_url, params=params)

#             if response.status == 200:
#                 search_results = response.json()[0]
#             else:
#                 # Handle API request errors
#                 search_results = []

#         context = {
#             'search_results': search_results
#         }
        
#         return render(request, 'staff/search_books.html', context)


#     return render(request, 'staff/search_books.html')