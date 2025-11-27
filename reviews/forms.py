from django import forms
from .models import Review

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