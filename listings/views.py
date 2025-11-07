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
    """
    Returns a "TESTING" message to the webpage. 
    """
    return HttpResponse("TESTING")


def select_p_type(request: HttpRequest, next_url="search/"):
    """
    Loads page for selecting a product type.
    
    Args:
        request (HttpRequest): Incoming HTTP request.
        next_url (str): URL that will be loaded after the form has been
            submitted.
    
    Returns:
        HttpResponse: The rendered "select_p_type.html" template with
            a selected next URL.
    """
    return render(request, "select_p_type.html", context={"next_url": next_url})


def search_listings(request: HttpRequest, p_type: str):
    """
    Handles searching for listings.
    
    NOT IMPLEMENTED. Need to add "listing_search.html" template.
    
    Args:
        request (HttpRequest): Incoming HTTP request. May include query
            parameters like 'q' and other filters.
        p_type (str): The name of a model class in the "products" app 
            that represents a subclass of Product.
    
    Returns:
        HttpResponse: The rendered "listing_search.html" template with
            search results based on the query and set filters.
    
    Raises:
        ValueError: If "p_type" does not match any subclass of Product.
    """
    # TODO: Implement this view
    product_model: type[Product] = load_product_model(p_type)
    
    query = request.GET.get("q")
    if query:
        query = unquote(query)
    
    
    listings_of_P = Listing.objects.filter(product_type=p_type)
    
    for listing in listings_of_P:
        print(listing.title)
    
    return HttpResponse("SEARCH LISTINGS")


def load_product_model(product_type_str: str):
    """
    Loads a Django product model class by name or raises a value error.
    
    Args:
        product_type_str (str): The name of a model class in the
            "products" app that should represent a subclass of Product.
    
    Returns:
        type[Product]: The corresponding Product subclass.
    
    Raises:
        ValueError: If the input string does not represent a subclass of
            Product.
    """
    product_model = apps.get_model("products", product_type_str)
    if not issubclass(product_model, Product):
        # TODO: We may want to just load a different page instead of raising a value error.
        raise ValueError(f"{product_type_str} is not a Product subclass")
    return product_model

def search_products(request: HttpRequest, p_type: str):
    """
    Handles searching for products when creating a listing.
    
    This view expects a 'q' query parameter and other filters (to be
    added later) in the URL. It loads the proper Product subclass,
    performs a fuzzy search on the subclass, and renders the search
    results.
    
    Args:
        request (HttpRequest): Incoming HTTP request. May include query
            parameters like 'q' and other filters.
        p_type (str): The name of a model class in the "products" app 
            that represents a subclass of Product.
    
    Returns:
        HttpResponse: The rendered "product_search.html" template with
            search results based on the query and set filters.
    
    Raises:
        ValueError: If "p_type" does not match any subclass of Product.
    """
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
    Handles creating listings based off a given product.
    
    This view processes a listing creation form submitted via a POST
    request. If it receives a valid form, a new Listing record is added,
    and it redirects to the new listing's page. If the form is invalid
    or not provided, the form is re-rendered.
    
    Args:
        request (HttpRequest): Incoming HTTP request. Contains form data.
        p_type (str): The name of a model class in the "products" app 
            that represents a subclass of Product.
        p_id (int): The ID of the product the listing is based on.

    Returns:
        HttpResponse: Renders the "listing_form.html" template if the
            form is invalid or missing. Redirects to the
            "load_listing_page" view if the form submission is valid.
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
    """
    Loads the listing page of the provided listing ID.
    
    Args:
        request (HttpRequest): Incoming HTTP request.
        l_id (int): The ID of the listing.
    
    Returns:
        HttpResponse: Renders template "listing_page.html" using the
            provided listing.
    
    Raises:
        Http404: If there is no listing with the provided ID.
    """
    listing = get_object_or_404(Listing, id=l_id)
    return render(request, "listing_page.html", context={"listing": listing})
