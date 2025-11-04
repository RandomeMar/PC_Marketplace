from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.apps import apps
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product, ProductQuerySet
from .models import Listing
from .forms import ListingForm
from urllib.parse import unquote

# Create your views here.

def test(request: HttpRequest):
    return HttpResponse("TESTING")


def select_p_type(request: HttpRequest, next_url="search/"):
    return render(request, "select_p_type.html", context={"next_url": next_url})


def search_listings(request: HttpRequest, p_type: str):
    # TODO: Implement search_listings
    return HttpResponse("SEARCH LISTINGS")


def load_product_model(product_type_str: str):
    product_model = apps.get_model("products", product_type_str)
    if not issubclass(product_model, Product):
        # TODO: We may want to just load a different page instead of raising a value error.
        raise ValueError(f"{product_type_str} is not a Product subclass")
    return product_model

def search_products(request: HttpRequest, p_type: str):
    product_model: type[Product] = load_product_model(p_type)
    
    query = request.GET.get("q")
    if query:
        query = unquote(query)
        
    p_filters = {} # TODO: Get filter values from template
    matched_products: list[Product] = product_model.objects.filter(**p_filters).fuzzy_search(query)
    
    context = {
        "p_type": p_type,
        "products": matched_products,
        "query": query
    }
    
    return render(request, "product_search.html", context)


def create_listing(request: HttpRequest, p_type: str, p_id: int):
    """
    1. Load the listing_form
    2. Make sure its valid, if not return the form
    3. If the form is valid add a listing record and render the listing page
    """
    # This is temp since we don't have our accounts system setup yet
    User = get_user_model()
    test_user, _ = User.objects.get_or_create(username="testuser")
    
    
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.product_id = p_id
            listing.owner = test_user # This is temp since we don't have our accounts system setup yet
            listing.save()
            return redirect("listings:load_listing_page", l_id=listing.id)
    else:
        form = ListingForm()
    return render(request, "listing_form.html", context={"form": form})


def load_listing_page(request: HttpRequest, l_id: int):
    listing = get_object_or_404(Listing, id=l_id)
    return render(request, "listing_page.html", context={"listing": listing})
