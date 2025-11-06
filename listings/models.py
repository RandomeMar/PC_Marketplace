from django.db import models
from django.conf import settings
from products.models import Product

# Create your models here.
class Listing(models.Model):
    """
    A Django model representing a product listing.
    
    This model stores the owner, product, title, listing text, condition,
    price, stock, and upload timestamp.
     
    Attributes:
        CONDITION_CHOICES (list[(str, str)]): Choices for the "condition"
            field.
        owner (type[AUTH_USER_MODEL]): Foreign key to the User model
            representing the listing owner.
        product (type[Product]): Foreign key to the Product subclass
            representing the listed product.
        title (type[CharField]): Title of the listing (max 100 chars).
        listing_text (type[TextField]): Listing description.
        condition (type[CharField]): Product condition. Must be one of
            "CONDITION_CHOICES".
        price (type[DecimalField]): Price per item in the listing.
        stock (type[PositiveIntegerField]): Number of items available.
        upload_time (type[DateTimeField]): Timestamp of listing creation.
    """
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