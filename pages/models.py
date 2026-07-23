from django.db import models

class CatalogueDataDownloadStat(models.Model):
    name = models.CharField(max_length=50, unique=True, default="catalogue_csv")
    total_downloads = models.PositiveIntegerField(default=0)
    last_downloaded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "catalogue data download stat"
        verbose_name_plural = "catalogue data download stats"

    def __str__(self):
        return f"{self.name}: {self.total_downloads} downloads"