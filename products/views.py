from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def all_listings_page(request):
    # Logic to fetch listings or any other homepage content
    return render(request, 'index.html')  # Use your actual homepage template