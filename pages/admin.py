from django.contrib import admin
from .models import CatalogueDataDownloadStat


@admin.register(CatalogueDataDownloadStat)
class CatalogueDataDownloadStatAdmin(admin.ModelAdmin):
    list_display = ("name", "total_downloads", "last_downloaded_at")
    readonly_fields = ("name", "total_downloads", "last_downloaded_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False