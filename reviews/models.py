from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from django.contrib.auth.models import User
from listings.models import Listing

# Create your models here.
class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="reviews")

    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    comment = models.TextField(blank=True, null=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer.username} gave {self.listing.product.product_name} {self.rating}/5 stars"