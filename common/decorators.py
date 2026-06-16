# a decorator to ensure a request is AJAX
from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        messages.warning(request, "You do not have permission to access that page.")
        return redirect("account_home")

    return _wrapped_view