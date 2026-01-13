import time
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
# from books.choices import language_choices
# from books.models import Book
# from blog.models import Post
from .forms import ContactForm

def send_formatted_email(data):
    subject = f"Library contact from {data['name']}"

    html_content = render_to_string('emails/contact_message.html', { 'data': data})

    text_content = strip_tags(html_content)

    send_mail(
        subject,
        text_content,
        settings.EMAIL_HOST_USER,
        ['sb1664@gmail.com'],
        html_message=html_content,
        fail_silently=False,
    )

def index(request):
	# redirecting home page to books
	# if 1 == 1:
	# 	return redirect('books')
	# else:
	# 	# books = Book.objects.filter(is_featured=True)[:3]
	# 	latest_posts = Post.published.all()[:3]

	# 	context = {
	# 		#'books': books,
	# 		'latest_posts': latest_posts,
	# 		'language_choices': language_choices,
	# 	}

	# 	return render(request, 'pages/index.html', context)
	return render(request, 'pages/index.html')

def about(request):
	return render(request, 'pages/about.html')

def contact(request):
    last_submit = request.session.get('contact_last_submit')
    if last_submit and time.time() - last_submit < 30:
        messages.error(request, "Please wait a moment before sending another message.")
        return redirect('index')

    if request.method == 'POST':
        form = ContactForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            send_formatted_email(data)

            request.session["contact_last_submit"] = time.time()
            return redirect('contact_thanks')
    
    else:
        form = ContactForm()
        
    return render(request, 'pages/contact.html', {'form': form})

def contact_thanks(request):
    return render(request, 'pages/contact_thanks.html')