from django import forms
from .models import Listing

class ListingForm(forms.ModelForm):
    """
    A Django ModelForm for the Listing Model
    """
    class Meta:
        model = Listing
        fields = [
            "title",
            "listing_text",
            "condition",
            "price",
            "stock"
        ]