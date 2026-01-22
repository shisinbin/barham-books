import requests
import os
import io
import json
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from books.models import BookInstance2, Book, Series, Category, BookTags
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
    users = User.objects.order_by(Lower('username'))
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

from .forms import StaffUserEditForm#, StaffProfileEditForm
@staff_member_required
def staff_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user_form = StaffUserEditForm(instance=user,
                                 data=request.POST)
        # profile_form = StaffProfileEditForm(
        #                             instance=user.profile,
        #                             data=request.POST,
        #                             files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            # profile_form.save()
            messages.success(request, 'The profile has been updated')
            return redirect('user', user_id)
    else:
        user_form = StaffUserEditForm(instance=user)
        # profile_form = StaffProfileEditForm(
        #                             instance=user.profile)
    context = {
        'user_form': user_form,
        # 'profile_form': profile_form,
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


# ---------- NEW IMPLEMENTATIONS 2026

from django.views.generic import FormView
from django.views import View
from django.utils.decorators import method_decorator

from .forms import StaffBookLookupForm, BookDraftForm
from .services.book_lookup import search_google_books
from .services.normalisers import normalise_google_books_results
from .services.covers import build_cover_candidates

SESSION_KEY = "staff_add_book"

def get_wizard_context(request, current_step):
    session = request.session.get(SESSION_KEY, {})

    steps = [
        {"key": "lookup", "label": "Lookup"},
        {"key": "select", "label": "Select"},
        {"key": "entry", "label": "Entry"},
        {"key": "review", "label": "Review"},
    ]

    completed = []
    for step in steps:
        if step["key"] == current_step:
            break
        completed.append(step["key"])
    
    return {
        "wizard": {
            "steps": steps,
            "current": current_step,
            "completed": completed,
            "source": session.get("selected", {}).get("source"),
        }
    }

@method_decorator(staff_member_required, name="dispatch")
class AddBookLookupView(FormView):
    template_name = "staff/book_add_lookup.html"
    form_class = StaffBookLookupForm

    def form_valid(self, form):
        # Reset wizard state
        self.request.session.pop(SESSION_KEY, None)

        action = self.request.POST.get("action")

        # Manual entry shortcut
        if action == "manual":
            self.request.session[SESSION_KEY] = {
                "lookup": {},
                "results": [],
                "selected": {
                    "index": None,
                    "source": "manual",
                },
            }
            self.request.session.modified = True
            return redirect("book_add_edit")

        lookup_data = form.cleaned_data

        try:
            raw = search_google_books(**lookup_data)
            results = normalise_google_books_results(raw)
        except (requests.RequestException, ValueError):
            messages.error(self.request, "Error contacting book data provider.")
            return self.form_invalid(form)

        # Store base session state
        self.request.session[SESSION_KEY] = {
            "lookup": lookup_data,
            "results": results,
            "selected": {
                "index": None,
                "source": None,
            },
        }

        # ISBN - exactly one result
        if lookup_data.get('isbn') and len(results) == 1:
            self.request.session[SESSION_KEY]["selected"] = {
                "index": 0,
                "source": "google_books",
            }
            self.request.session.modified = True
            return redirect("book_add_edit")
        
        # Multiple results
        if results:
            self.request.session.modified = True
            return redirect("book_add_select")

        # No results
        messages.info(
            self.request,
            "No results found. Try again or proceed to manual entry."
        )
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_wizard_context(self.request, "lookup"))
        return context

class AddBookSelectView(View):
    template_name = "staff/book_add_select.html"

    def get(self, request):
        session_data = request.session.get(SESSION_KEY)

        if not session_data:
            messages.error(request, "Your session expired. Start again.")
            return redirect("book_add_lookup")

        results = session_data.get('results')
        if not results:
            messages.error(request, "No results found. Start again")
            return redirect("book_add_lookup")

        context = get_wizard_context(self.request, "select")
        context.update({"results": results})
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        session_data = request.session.get(SESSION_KEY)

        if not session_data:
            messages.error(request, "Your session expired. Start again.")
            return redirect("book_add_lookup")
        
        choice = request.POST.get("choice")

        if choice == "manual":
            session_data["selected"]["index"] = None
            session_data["selected"]["source"] = "manual"
        
        else:
            try:
                index = int(choice)
            except (TypeError, ValueError):
                messages.error(request, "Invalid selection")
                return redirect("book_add_select")
            
            results = session_data.get("results", [])
            if index < 0 or index >= len(results):
                messages.error(request, "Invalid selection")
                return redirect("book_add_select")
            
            session_data["selected"]["index"] = index
            session_data["selected"]["source"] = "google_books"
        
        request.session.modified = True
        return redirect("book_add_edit")

from .helpers import choose_best_isbn, save_temp_uploaded_file

class AddBookEditView(FormView):
    template_name = "staff/book_add_edit.html"
    form_class = BookDraftForm

    def _serialize_book_data(self, cleaned_data):
        data = cleaned_data.copy()

        # ModelChoiceField → store PK
        if data.get("category"):
            data["category_id"] = data["category"].pk
        data.pop("category", None)

        if data.get("series_existing"):
            data["series_existing_id"] = data["series_existing"].pk
        data.pop("series_existing", None)

        # ModelMultipleChoiceField → store list of PKs
        tags = data.get("book_tags")
        if tags:
            data["book_tag_ids"] = [t.pk for t in tags]
        else:
            data["book_tag_ids"] = []
        data.pop("book_tags", None)

        photo = data.get("photo")
        if photo:
            temp_path, temp_url = save_temp_uploaded_file(photo)
            data["photo_path"] = temp_path
            data["photo_url"] = temp_url
            data["photo"] = None

        return data


    def get_initial(self):
        initial = {
            "language": "English",
            "category": Category.objects.filter(code="GEN").first(),
        }

        session_data = self.request.session.get(SESSION_KEY)
        # print(session_data)
        if not session_data:
            return initial

        selected = session_data.get("selected", {})
        if selected.get("source") != "google_books":
            return initial
        
        idx = selected.get("index")
        results = session_data.get("results", [])

        if idx is None or idx >= len(results):
            return initial
        
        book = results[idx]

        title = book.get("title", "")
        subtitle = book.get("subtitle")
        if subtitle:
            title = f"{title}: {subtitle}"
        
        authors = book.get("authors") or []
        author = authors[0] if authors else ""

        isbn = book.get("isbn13") or book.get("isbn10") or ""

        initial.update({
            "title": title,
            "author": author,
            "isbn": isbn,
            "year": book.get("published_year"),
            "pages": book.get("page_count"),
            "publisher": book.get("publisher"),
            "summary": book.get("description"),
        })
        
        categories = book.get("categories")
        if categories:
            self.tag_hint = ", ".join(categories)
        
        return initial
    
    def form_valid(self, form):
        print(form.cleaned_data)
        session_data = self.request.session.get(SESSION_KEY)
        
        if not session_data:
            messages.error(self.request, "Your session expired.")
            return redirect("book_add_lookup")

        # session_data["book_data"] = form.cleaned_data
        session_data["book_data"] = self._serialize_book_data(form.cleaned_data)
        self.request.session.modified = True

        return redirect("book_add_confirm")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_wizard_context(self.request, "entry"))

        if hasattr(self, 'tag_hint'):
            context['tag_hint'] = self.tag_hint

        return context

from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.storage import default_storage

class AddBookConfirmView(View):
    template_name = "staff/book_add_confirm.html"

    def get(self, request):
        session_data = request.session.get(SESSION_KEY)
        
        if not session_data or "book_data" not in session_data:
            messages.error(request, "Your session expired.")
            return redirect("book_add_lookup")

        raw_book_data = session_data["book_data"]
        book_data = self._hydrate_book_data(raw_book_data)

        title = book_data["title"]

        author = self._find_existing_author(book_data)
        duplicate_book = self._find_duplicate_book(book_data, author)
        series_warning = self._check_series_number_conflict(book_data)

        print(book_data)

        context = get_wizard_context(self.request, "review")
        context.update({
            "tentative_book": book_data,
            "tentative_author": author,
            "duplicate_book": duplicate_book,
            "series_warning": series_warning,
            "can_confirm": not duplicate_book,
            "photo_url": book_data.get("photo_url"),
        })
        return render(request, self.template_name, context)

    def post(self, request):
        session_data = request.session.get(SESSION_KEY)

        if not session_data or "book_data" not in session_data:
            messages.error(request, "Your session expired.")
            return redirect("book_add_lookup")

        raw_book_data = session_data["book_data"]
        book_data = self._hydrate_book_data(raw_book_data)

        try:
            with transaction.atomic():
                author = self._get_or_create_author(book_data)
                self._assert_no_duplicate_book(book_data, author)

                series = self._get_or_create_series(book_data)

                book = self._create_book(book_data, author, series)
                self._add_tags(book, book_data)
                self._create_book_instance(book, book_data)

        except (ValidationError, IntegrityError) as e:
            messages.error(request, str(e))
            return redirect("book_add_confirm")

        del request.session[SESSION_KEY]
        messages.success(request, "Book added successfully.")
        return redirect(book)

    # ---------- get helpers ----------

    def _hydrate_book_data(self, book_data):
        data = book_data.copy()

        # Category
        category_id = data.get("category_id")
        if category_id:
            data["category"] = Category.objects.get(pk=category_id)

        # Series
        series_id = data.get("series_existing_id")
        if series_id:
            data["series_existing"] = Series.objects.get(pk=series_id)
        else:
            data["series_existing"] = None

        # Tags
        tag_ids = data.get("book_tag_ids", [])
        if tag_ids:
            data["book_tags"] = BookTags.objects.filter(pk__in=tag_ids)
        else:
            data["book_tags"] = BookTags.objects.none()

        return data


    def _find_existing_author(self, book_data):
        author_name = book_data["author"]
        parts = author_name.split()
        return Author.objects.filter(
            first_name__iexact=parts[0],
            last_name__iexact=parts[-1],
        ).first()

    def _find_duplicate_book(self, book_data, author):
        if not author:
            return None
        return Book.objects.filter(
            title__iexact=book_data["title"],
            author=author,
        ).first()

    def _check_series_number_conflict(self, book_data):
        series = book_data.get("series_existing")
        num = book_data.get("series_num")

        if not series or not num:
            return None
        
        return Book.objects.filter(
            series=series,
            series_num=num,
        ).first()

    # ---------- post helpers ----------

    def _get_or_create_author(self, book_data):
        author_name = book_data["author"]
        parts = author_name.split()
        first_name, *middle_names_list, last_name = parts
        middle_names = " ".join(middle_names_list)
        author, _ = Author.objects.get_or_create(
            first_name=first_name,
            middle_names=middle_names,
            last_name=last_name,
        )
        return author

    def _assert_no_duplicate_book(self, book_data, author):
        if Book.objects.filter(
            title__iexact=book_data["title"],
            author=author,
        ).exists():
            raise ValidationError("This book already exists.")

    def _get_or_create_series(self, book_data):
        series = book_data.get("series_existing")
        new_name = book_data.get("series_new", "").strip()

        if series:
            return series

        if new_name:
            series, _ = Series.objects.get_or_create(name=new_name)
            return series

    def _get_series_number(self, book_data, series):
        num = book_data.get("series_num")

        if not series:
            return None
        
        if num:
            return num
        
        # Default
        return 99

    def _create_book(self, book_data, author, series):
        photo_file = None
        temp_path = book_data.get("photo_path")

        if temp_path and default_storage.exists(temp_path):
            photo_file = File(default_storage.open(temp_path))

        book = Book.objects.create(
            title=book_data["title"],
            author=author,
            summary=book_data.get("summary", ""),
            series=series,
            series_num=self._get_series_number(book_data, series),
            category=book_data["category"],
            photo=photo_file,
            year=book_data.get("year"),
            is_featured=book_data.get("is_featured", False),
        )

        # Cleanup temp file
        if temp_path:
            default_storage.delete(temp_path)

        return book
    
    def _add_tags(self, book, book_data):
        tags = book_data.get("book_tags")
        if tags:
            book.book_tags.add(*tags)

    def _split_isbn(self, isbn):
        if not isbn:
            return None, None
        
        if len(isbn) == 10:
            return isbn, None

        if len(isbn) == 13:
            return None, isbn

        return None, None

    def _create_book_instance(self, book, book_data):
        isbn10, isbn13 = self._split_isbn(book_data.get("isbn"))

        BookInstance2.objects.create(
            book=book,
            pages=book_data.get("pages"),
            isbn10=isbn10,
            isbn13=isbn13,
            publisher=book_data.get("publisher", ""),
            book_type=book_data["book_type"],
        )

from django.urls import reverse

@staff_member_required
def book_cover_lookup_page(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    # Safeguard
    if book.photo:
        messages.error(request, 'This book already has a cover image.')
        return redirect(book)

    context = {
        "book_without_cover_image": book,
        "api_candidates_url": reverse("lookup_book_cover_candidates", args=[book.id]),
        "api_attach_url": reverse("attach_book_cover", args=[book.id]),
        "book_detail_url": book.get_absolute_url(),
    }

    return render(request, 'staff/book_cover_lookup.html', context)


# PROBE_COVERS = False
# MAX_PROBES = 10
# COVER_TIMEOUT = 2

@staff_member_required
@require_GET
def lookup_book_cover_candidates(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if book.photo:
        return JsonResponse({
            "ok": False,
            "error": "Book already has a cover image."
        }, status=400)

    candidates = build_cover_candidates(book)

    # if PROBE_COVERS:
    #     candidates = _filter_working_covers(candidates)

    return JsonResponse({
        "ok": True,
        "book": {
            "id": book.id,
            "title": book.title,
            "author": (
                f"{book.author.first_name} {book.author.last_name}"
                if book.author else None
            ),
        },
        "candidates": candidates,
    })


# def _filter_working_covers(candidates):
#     working = []
#     probes = 0

#     for item in candidates:
#         if probes >= MAX_PROBES:
#             break

#         url = item["url"]
#         probes += 1

#         try:
#             resp = requests.head(url, timeout=COVER_TIMEOUT)
#             if resp.status_code == 200:
#                 working.append(item)
#         except requests.RequestException:
#             continue

#     return working

MAX_IMAGE_BYTES = 1 * 1024 * 1024  # 1MB
FETCH_TIMEOUT = 8
ALLOWED_HOST = "covers.openlibrary.org"

@staff_member_required
@require_POST
# @csrf_exempt
def attach_book_cover(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if book.photo:
        return JsonResponse({
            "ok": False,
            "error": "Book already has a cover image."
        }, status=400)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        cover_url = payload.get("cover_url")
    except Exception:
        return JsonResponse({
            "ok": False,
            "error": "Invalid JSON payload."
        }, status=400)

    if not cover_url:
        return JsonResponse({
            "ok": False,
            "error": "Missing cover_url."
        }, status=400)

    if ALLOWED_HOST not in cover_url:
        return JsonResponse({
            "ok": False,
            "error": "Only OpenLibrary cover URLs are allowed."
        }, status=400)

    try:
        resp = requests.get(cover_url, timeout=FETCH_TIMEOUT, stream=True)
        resp.raise_for_status()
    except requests.RequestException:
        return JsonResponse({
            "ok": False,
            "error": "Failed to fetch image from OpenLibrary."
        }, status=400)

    content_type = resp.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        return JsonResponse({
            "ok": False,
            "error": "URL did not return an image."
        }, status=400)

    # Read with size cap
    data = bytearray()
    for chunk in resp.iter_content(chunk_size=8192):
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > MAX_IMAGE_BYTES:
            return JsonResponse({
                "ok": False,
                "error": "Image exceeds 1MB limit."
            }, status=400)

    # Derive filename
    ext = content_type.split("/")[-1].lower()
    if ext not in ("jpeg", "jpg", "png", "webp"):
        ext = "jpg"

    filename = f"cover_{book.id}.{ext}"

    book.photo.save(filename, ContentFile(bytes(data)), save=True)

    return JsonResponse({ "ok": True })

@staff_member_required
@require_GET
def google_books_probe(request):
    """
    Very simple probe endpoint for Google Books API.

    Query params supported:
      - title
      - author
      - isbn
      - q      (raw query override)
      - max    (maxResults, default 5)
    """

    title = request.GET.get("title")
    author = request.GET.get("author")
    isbn = request.GET.get("isbn")
    raw_q = request.GET.get("q")
    max_results = request.GET.get("max", "5")

    # Build query
    q_parts = []

    if raw_q:
        q = raw_q
    else:
        if isbn:
            q_parts.append(f"isbn:{isbn}")

        if title:
            q_parts.append(f'intitle:"{title}"')

        if author:
            q_parts.append(f'inauthor:"{author}"')

        q = " ".join(q_parts)

    if not q:
        return JsonResponse(
            {"ok": False, "error": "Provide at least one of: title, author, isbn, or q"},
            status=400,
        )

    params = {
        "q": q,
        "maxResults": max_results,
        "key": settings.GOOGLE_BOOKS_API_KEY,
    }

    try:
        resp = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

    except requests.RequestException as exc:
        return JsonResponse(
            {"ok": False, "error": f"Request failed: {exc}"},
            status=502,
        )
    except ValueError:
        return JsonResponse(
            {"ok": False, "error": "Invalid JSON from Google Books"},
            status=502,
        )

    # Log some useful high-level info to console
    total = data.get("totalItems")
    items = data.get("items") or []

    print("=== GOOGLE BOOKS PROBE ===")
    print("Query:", q)
    print("Total items:", total)
    print("Returned items:", len(items))
    if items:
        info = items[0].get("volumeInfo", {})
        print("Top result title:", info.get("title"))
        print("Top result authors:", info.get("authors"))
        print("==========================")

    return JsonResponse(
        {
            "ok": True,
            "query": q,
            "totalItems": total,
            "returnedItems": len(items),
            "raw": data,
        }
    )