from django.db import models
from django.utils import timezone

# Create your models here.
class Product(models.Model):
    CATEGORY_CHOICES = [
        ("CPU", "CPU"),
        ("GPU", "GPU"),
        ("MB", "Motherboard"),
        ("RAM", "Memory"),
        ("PSU", "Power Supply"),
        ("STORAGE", "Storage"),
        ("CASE", "Case"),
        ("MISC", "Miscellaneous"),
    ]
    
    product_name = models.CharField(max_length=255)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=10)
    ext_source = models.CharField(max_length=255) # TODO: Figure out APIs/DBs
    ext_id = models.CharField(max_length=100) # TODO: Figure out API ID lengths
    specs = models.JSONField()
    last_synced = models.DateTimeField(default=timezone.now)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["ext_source", "ext_id"], name="unique_ext_source_ext_id") # Ensures no duplicate products from DB
        ]