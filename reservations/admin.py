from django.contrib import admin

from .models import Reservation

#admin.site.register(Reservation)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
	list_display = ('user_id', 'book', 'reservation_date')
	list_display_links = ('user_id', 'book')
	list_per_page = 25
	search_fields = ('book',)