from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
	path('', include('pages.urls')),
	path('books/', include('books.urls')),
	path('authors/', include('authors.urls')),
	path('accounts/', include('accounts.urls')),
	path('reservations/', include('reservations.urls')),
	path('staff/', include('staff.urls')),
	path('blog/', include('blog.urls')),
	path('legacy/', include('legacy.urls')),
    path('users/', include('books.user_urls')),
    #path('select2/', include('django_select2.urls')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
