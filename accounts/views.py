from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from books.models import Book
from .forms import RegisterForm

class CustomLoginView(LoginView):
    template_name = "accounts/login.html"

    def form_valid(self, form):
        messages.success(self.request, "You are now logged in.")
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have been logged out.")
        return super().dispatch(request, *args, **kwargs)

class CustomPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("account_home")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been updated.")
        return super().form_valid(form)

def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])
        user.save()
        login(request, user)
        messages.success(request, "Account created successfully.")
        next_url = request.GET.get("next")
        return redirect(next_url or "account_home")

    return render(request, "accounts/register.html", {"form": form})

@login_required
def account_home(request):
    liked_books = request.user.books_liked.all()
    interested_books = Book.objects.filter(interests__user=request.user)
    reviews = request.user.reviews.filter(active=True).order_by('-updated')
    review_nums = [1, 2, 3, 4, 5]
    return render(request, "accounts/account_home.html", {
        "liked_books": liked_books,
        "interested_books": interested_books,
        "reviews": reviews,
        "review_nums": review_nums,
    })
