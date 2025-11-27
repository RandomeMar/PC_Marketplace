from django import forms
from .models import Listing, ListingImage, Review

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
            "stock",
            #"status",
            "location_city",
            "location_state",
            "zip_code",
            "shipping_available",
            "local_pickup_only",
            "shipping_cost",
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Intel Core i7-12700K - Excellent Condition'
            }),
            'listing_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Describe your product in detail. Include any defects, usage history, etc.'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'location_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'location_state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Zip Code'
            }),
            'shipping_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
        }
        labels = {
            'shipping_available': 'Offer Shipping',
            'local_pickup_only': 'Local Pickup Only',
        }


class ListingImageForm(forms.ModelForm):
    #image listings form
    class Meta:
        model = ListingImage
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional image caption'
            }),
        }


# handles multiple images
from django.forms import inlineformset_factory

ListingImageFormSet = inlineformset_factory(
    Listing,
    ListingImage,
    form=ListingImageForm,
    extra=5, 
    max_num=10,
    can_delete=True
)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review

        fields = ['rating', 'comment']

        widgets = {'title': forms.RadioSelect(choices=[
            (1,     '1'),
            (1.5,   '1.5'),
            (2,     '2'),
            (2.5,   '2.5'),
            (3,     '3'),
            (3.5,   '3.5'),
            (4,     '4'),
            (4.5,   '4.5'),
            (5,     '5'),
            ])}