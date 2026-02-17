import time
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from smtplib import SMTPException
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages

from books.collections import COLLECTIONS
from .forms import ContactForm

def send_formatted_email(data) -> bool:
    """
    Returns True if the email was sent successfully, otherwise False.
    """
    subject = f"Library contact from {data['name']}"

    html_content = render_to_string('emails/contact_message.html', { 'data': data })

    text_content = strip_tags(html_content)

    reply_to = [data["email"]] if data.get("email") else None

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=settings.EMAIL_STAFF_RECIPIENTS,
            reply_to=reply_to,
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True

    except SMTPException:
        return False

def home(request):
    featured_collections = {
        slug: c
        for slug, c in COLLECTIONS.items()
        if c.get("featured") is True
    }
    
    return render(request, 'pages/home_magazine.html', { 'featured_collections': featured_collections})

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

            sent_ok = send_formatted_email(data)

            if sent_ok:
                request.session["contact_last_submit"] = time.time()
                return redirect('contact_thanks')

            messages.error(request, "Sorry — we couldn't send your message right now. Please try again in a moment.")

    else:
        initial = {}
        if request.user.is_authenticated:
            initial["email"] = request.user.email
        form = ContactForm(initial=initial)
        
    return render(request, 'pages/contact.html', {'form': form})

def contact_thanks(request):
    return render(request, 'pages/contact_thanks.html')

def index(request):
    return render(request, 'pages/index.html')