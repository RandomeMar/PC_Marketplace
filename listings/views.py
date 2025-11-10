from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.apps import apps
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Min, Max, Model
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

def homepage(request: HttpRequest):
    print("test")
    return render(request, "homepage.html") 


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
    product_model: type[Product] = load_product_model(p_type)
    
    l_filter_vals = gather_filters(request, Listing)
    p_filter_vals = gather_filters(request, product_model, "product__")
    
    query = request.GET.get("q")
    if query:
        query = unquote(query)
    
    matched_listings = Listing.objects.filter(
        **l_filter_vals["str"], **l_filter_vals["int"], **l_filter_vals["bool"],
        **p_filter_vals["str"], **p_filter_vals["int"], **p_filter_vals["bool"]) # TODO: NO FUZZY SEARCH YET
    
    str_options, int_options, bool_options = build_filter_fields(Listing, l_filter_vals)
    str_options, int_options, bool_options = build_filter_fields(product_model, p_filter_vals, "product__")
    
    context = {
        "p_type": p_type,
        "listings": matched_listings,
        "query": query,
        "str_options": str_options,
        "int_options": int_options,
        "bool_options": bool_options,
    }
    
    return render(request, "listing_search.html", context)


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

def gather_filters(request: HttpRequest, model: type[Model], prefix="") -> dict:
    str_filters = {}
    int_filters = {}
    float_filters = {}
    bool_filters = {}
    
    # Gets filter values from GET.
    for field in model._meta.get_fields():
        if not field.concrete or field.is_relation:
            continue
        if field.get_internal_type() == "PositiveIntegerField":
            # Integer field
            min_val = request.GET.get(f"{field.name}_min")
            max_val = request.GET.get(f"{field.name}_max")
            
            try:
                if min_val is None or min_val == "":
                    raise ValueError
                int_filters[f"{prefix}{field.name}__gte"] = int(min_val)
            except ValueError:
                pass
            try:
                if max_val is None or max_val == "":
                    raise ValueError
                int_filters[f"{prefix}{field.name}__lte"] = int(max_val)
            except ValueError:
                pass
        
        elif field.get_internal_type() == "DecimalField":
            # Float/Decimal field
            min_val = request.GET.get(f"{field.name}_min")
            max_val = request.GET.get(f"{field.name}_max")
            
            try:
                if min_val is None or min_val == "":
                    raise ValueError
                float_filters[f"{prefix}{field.name}__gte"] = float(min_val)
            except ValueError:
                pass
            try:
                if max_val is None or max_val == "":
                    raise ValueError
                float_filters[f"{prefix}{field.name}__lte"] = float(max_val)
            except ValueError:
                pass
            
            
        
        elif field.get_internal_type() == "BooleanField":
            # Boolean field
            value = request.GET.get(field.name)
            if value == "True":
                bool_filters[f"{prefix}{field.name}"] = True
            elif value == "False":
                bool_filters[f"{prefix}{field.name}"] = False
        
        else:
            # String field
            values = request.GET.getlist(field.name)
            if values:
                str_filters[f"{prefix}{field.name}__in"] = values
        
                
    return {"str": str_filters, "int": int_filters, "float": float_filters, "bool": bool_filters}

def build_filter_fields(model: type[Model], filter_vals: dict[dict], prefix="") -> dict[dict]:
    str_options = {}
    int_options = {}
    float_options = {}
    bool_options = {}
    
    # Gets filter fields with options for the template.
    for field in model._meta.get_fields():
        if not field.concrete or field.is_relation:
            continue
        if field.name not in getattr(model, "FILTER_FIELDS", []):
            continue
        
        if field.get_internal_type() == "PositiveIntegerField":
            # Get int field options     
            
            min_max = model.objects.aggregate(
                min_val=Min(field.name),
                max_val=Max(field.name)
                )
            int_options[field.name] = {
                "label": field.verbose_name,
                "min_val": min_max["min_val"],
                "max_val": min_max["max_val"],
            }
            if filter_vals["int"].get(f"{prefix}{field.name}__gte"):
                int_options[field.name]["user_min"] = filter_vals["int"][
                    f"{prefix}{field.name}__gte"]
            if filter_vals["int"].get(f"{prefix}{field.name}__lte"):
                int_options[field.name]["user_max"] = filter_vals["int"][
                    f"{prefix}{field.name}__lte"]
        
        elif field.get_internal_type() == "DecimalField":
            # Get float field options
            min_max = model.objects.aggregate(
                min_val=Min(field.name),
                max_val=Max(field.name)
                )
            float_options[field.name] = {
                "label": field.verbose_name,
                "min_val": min_max["min_val"],
                "max_val": min_max["max_val"],
            }
            if filter_vals["float"].get(f"{prefix}{field.name}__gte"):
                float_options[field.name]["user_min"] = filter_vals["float"][
                    f"{prefix}{field.name}__gte"]
            if filter_vals["float"].get(f"{prefix}{field.name}__lte"):
                float_options[field.name]["user_max"] = filter_vals["float"][
                    f"{prefix}{field.name}__lte"]
        
        elif field.get_internal_type() == "BooleanField":
            # Get bool field options
            bool_options[field.name] = {
                "label": field.verbose_name,
                "user_input": filter_vals["bool"].get(f"{prefix}{field.name}")
            }
        
        else:
            # Get string field options
            options = model.objects.values_list(field.name, flat=True).distinct().order_by(field.name)
            str_options[field.name] = {
                "label": field.verbose_name, 
                "options": options,
                "user_inputs": filter_vals["str"].get(f"{prefix}{field.name}__in")
                }
    return {
        "str": str_options, "int": int_options, "float": float_options,
        "bool": bool_options
        }

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
    filter_vals = gather_filters(request, product_model)
    
    query = request.GET.get("q")
    if query:
        query = unquote(query)
    
    matched_products: list[Product] = product_model.objects.filter(
        **filter_vals["str"], **filter_vals["int"], **filter_vals["bool"], **filter_vals["float"]).fuzzy_search(query)
    
    filter_fields = build_filter_fields(product_model, filter_vals)
    
    
    context = {
        "p_type": p_type,
        "products": matched_products,
        "query": query,
        "filter_fields": filter_fields,
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
