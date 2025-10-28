from django.db import models
from django.conf import settings
from products.models import Product

# Create your models here.
class Listing(models.Model):
    CONDITION_CHOICES = [
        ("new", "new"),
        ("refurb", "refurbished"),
        ("used", "used"),
        ("for_parts", "for parts")
    ]
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    title = models.CharField(max_length=100)
    listing_text = models.TextField()
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    upload_time = models.DateTimeField(auto_now_add=True)