from django.db import models
from django.conf import settings
from products.models import Product
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

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
        product_type (CharField): Name of the model "product" is. This
            attribute is automatically filled.
        title (CharField): Title of the listing (max 100 chars).
        listing_text (TextField): Listing description.
        condition (CharField): Product condition. Must be one of
            "CONDITION_CHOICES".
        price (DecimalField): Price per item in the listing.
        stock (PositiveIntegerField): Number of items available.
        upload_time (DateTimeField): Timestamp of listing creation.
    """
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('pending', 'Pending'),
        ('inactive', 'Inactive'),
    ]
    CONDITION_CHOICES = [
        ("new", "Brand New"),
        ("like_new", "Like New"),
        ("refurb", "refurbished"),
        ("used", "used"),
        ("for_parts", "for parts")
    ]
    
    #Relationships
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Owner")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    #Basic listing info
    title = models.CharField(max_length=100, verbose_name="Title")
    listing_text = models.TextField(verbose_name="Listing Text")
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, verbose_name="Condition")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    #locations
    location_city = models.CharField(max_length=100, blank=True, null=True)
    location_state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    
    # Shipping NOTE: For now I don't even know if we will have shipping, so I might get rid of this later
    shipping_available = models.BooleanField(default=True)
    local_pickup_only = models.BooleanField(default=False)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Timestamps
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name="Upload Time")
    
    FILTER_FIELDS = ["condition", "price"]
    
    class Meta:
        ordering = ['-upload_time']
        
    def __str__(self):
        return f"{self.title} - {self.product.product_name} - ${self.price}"
        
    
    
class ListingImage(models.Model):
    #Model for multiple images per listing
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_images/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-is_primary']

    def __str__(self):
        return f"Image for {self.listing.title}"

    def save(self, *args, **kwargs):
        # If this is set as primary, unset all other primary images for this listing
        if self.is_primary:
            ListingImage.objects.filter(listing=self.listing, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)
