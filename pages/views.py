import time
from smtplib import SMTPException
import json
import os
from datetime import timedelta

from django.db.models import F
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags

from books.collections import COLLECTIONS
from common.decorators import superuser_required
from .forms import ContactForm, CatalogueDataDownloadForm
from .models import CatalogueDataDownloadStat


def index(request):
    return render(request, 'pages/index.html')

def about(request):
	return render(request, 'pages/about.html')

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


# ---------- Magazine-style homepage ----------

@superuser_required
def home(request):
    featured_collections = {
        slug: c
        for slug, c in COLLECTIONS.items()
        if c.get("featured") is True
    }
    
    return render(request, 'pages/home_magazine.html', { 'featured_collections': featured_collections})


# ---------- Custom error pages ----------

def custom_403(request, exception):
    return render(request, "403.html", status=403)

def custom_404(request, exception):
    return render(request, "404.html", status=404)

def custom_500(request):
    return render(request, "500.html", status=500)


# ---------- Data download page ----------

def get_catalogue_export_paths():
    csv_path = os.path.join(
        settings.PRIVATE_EXPORT_ROOT,
        settings.BOOK_EXPORT_FILENAME,
    )

    metadata_path = os.path.join(
        settings.PRIVATE_EXPORT_ROOT,
        settings.BOOK_EXPORT_METADATA_FILENAME,
    )

    return csv_path, metadata_path

def load_catalogue_export_info():
    csv_path, metadata_path = get_catalogue_export_paths()

    info = {
        "available": False,
        "csv_path": csv_path,
        "filename": settings.BOOK_EXPORT_FILENAME,
        "generated_at": None,
        "row_count": None,
        "is_stale": False,
    }

    if not os.path.exists(csv_path) or not os.path.exists(metadata_path):
        return info

    try:
        with open(metadata_path, "r", encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
    except (OSError, json.JSONDecodeError):
        return info

    generated_at = None
    generated_at_raw = metadata.get("generated_at")

    if generated_at_raw:
        generated_at = parse_datetime(generated_at_raw)

        if generated_at and timezone.is_naive(generated_at):
            generated_at = timezone.make_aware(generated_at)

        if generated_at:
            generated_at = timezone.localtime(generated_at)

    is_stale = False
    if generated_at:
        stale_after = timedelta(days=settings.BOOK_EXPORT_STALE_AFTER_DAYS)
        is_stale = timezone.now() - generated_at > stale_after

    info.update({
        "available": True,
        "filename": metadata.get("filename", settings.BOOK_EXPORT_FILENAME),
        "generated_at": generated_at,
        "row_count": metadata.get("row_count"),
        "format": metadata.get("format", "csv"),
        "is_stale": is_stale,
    })

    return info

def get_download_filename(export_info):
    generated_at = export_info.get("generated_at")

    if generated_at:
        date_part = generated_at.date().isoformat()
        return f"barham-books-catalogue-{date_part}.csv"

    return settings.BOOK_EXPORT_FILENAME

def record_catalogue_data_download():
    stat, created = CatalogueDataDownloadStat.objects.get_or_create(
        name="catalogue_csv"
    )

    CatalogueDataDownloadStat.objects.filter(pk=stat.pk).update(
        total_downloads=F("total_downloads") + 1,
        last_downloaded_at=timezone.now(),
    )

def catalogue_data(request):
    export_info = load_catalogue_export_info()

    last_download = request.session.get("catalogue_data_last_download")
    if last_download and time.time() - last_download < settings.DATA_DOWNLOAD_COOLDOWN_SECONDS:
        messages.error(request, "Please wait a moment before downloading again.")
        return redirect("about")

    if request.method == "POST":
        form = CatalogueDataDownloadForm(request.POST)

        if form.is_valid():
            if not export_info["available"]:
                messages.error(request, "The catalogue data export is not available right now.")
                return redirect("catalogue_data")

            request.session["catalogue_data_last_download"] = time.time()

            record_catalogue_data_download()

            return FileResponse(
                open(export_info["csv_path"], "rb"),
                as_attachment=True,
                filename=get_download_filename(export_info),
                content_type="text/csv",
            )

    else:
        form = CatalogueDataDownloadForm()

    return render(request, "pages/catalogue_data.html", {
        "form": form,
        "export": export_info,
    })