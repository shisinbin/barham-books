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
from books.collections import COLLECTIONS

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
    featured_collections = {
        slug: c
        for slug, c in COLLECTIONS.items()
        if c.get("featured") is True
    }
    
    return render(request, 'pages/index.html', { 'featured_collections': featured_collections})

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
        initial = {}
        if request.user.is_authenticated:
            initial["email"] = request.user.email
        form = ContactForm(initial=initial)
        
    return render(request, 'pages/contact.html', {'form': form})

def contact_thanks(request):
    return render(request, 'pages/contact_thanks.html')

def home(request):
    return render(request, 'pages/home.html')