from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.apps import apps
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Min, Max
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
    
    p_filters = {} # Product filters (series, manufacturer, release_year, etc.)
    l_filters = {} # Listing filters (upload_time, price, stock, etc.)
    
    listings_of_P = Listing.objects.filter(product_type=p_type).filter(p_filters).filter(l_filters)
    
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
    
    This view expects a 'q' query parameter and other filters in the
    URL. It loads the proper Product subclass, performs a fuzzy search 
    on the subclass, and renders the search results.
    
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
    
    str_filters = {}
    int_filters = {}
    bool_filters = {}
    
    for field in product_model._meta.get_fields():
        if not field.concrete or field.is_relation:
            continue
        if field.get_internal_type() == "PositiveIntegerField":
            # Integer field
            min_val = request.GET.get(f"{field.name}_min")
            max_val = request.GET.get(f"{field.name}_max")
            
            if min_val is not None and min_val != "":
                int_filters[f"{field.name}__gte"] = int(min_val)
            if max_val is not None and max_val != "":
                int_filters[f"{field.name}__lte"] = int(max_val)
        elif field.get_internal_type() == "BooleanField":
            # Boolean field
            value = request.GET.get(field.name)
            if value == "True":
                bool_filters[field.name] = True
            elif value == "False":
                bool_filters[field.name] = False
        else:
            # String field
            values = request.GET.getlist(field.name)
            if values:
                str_filters[f"{field.name}__in"] = values

    
    query = request.GET.get("q")
    if query:
        query = unquote(query)
    
    matched_products: list[Product] = product_model.objects.filter(**str_filters, **int_filters).fuzzy_search(query)
    
    str_options = {}
    int_options = {}
    bool_options = {}
    
    # Gets all filter names along with their options
    for field in product_model._meta.get_fields():
        if not field.concrete or field.is_relation:
            continue
        if field.name not in getattr(product_model, "FILTER_FIELDS", []):
            continue
        
        if field.get_internal_type() == "PositiveIntegerField":
            # Get int field options
            min_max = product_model.objects.aggregate(
                min_val=Min(field.name),
                max_val=Max(field.name)
                )
            int_options[field.name] = {
                "label": field.verbose_name,
                "min_val": min_max["min_val"],
                "max_val": min_max["max_val"],
                "selected": [
                    int_filters.get(f"{field.name}__gte"),
                    int_filters.get(f"{field.name}__lte")
                    ]
            }
        elif field.get_internal_type() == "BooleanField":
            # Get bool field options
            bool_options[field.name] = {
                "label": field.verbose_name,
                "selected": bool_filters.get(field.name)
            }
        else:
            # Get string field options
            options = product_model.objects.values_list(field.name, flat=True).distinct().order_by(field.name)
            str_options[field.name] = {
                "label": field.verbose_name, 
                "options": options,
                "selected": str_filters.get(f"{field.name}__in")
                }
    
    
    context = {
        "p_type": p_type,
        "products": matched_products,
        "query": query,
        "str_options": str_options,
        "int_options": int_options,
        "bool_options": bool_options,
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
