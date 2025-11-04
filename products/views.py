from django.shortcuts import render
from django.apps import apps
from django.http import HttpRequest
from .models import Product
from requests import request
from rapidfuzz import process, fuzz
from urllib.parse import unquote

# Create your views here.

def load_product_model(product_type_str: str):
    product_model = apps.get_model("products", product_type_str)
    if not issubclass(product_model, Product):
        # TODO: We may want to just load a different page instead of raising a value error.
        raise ValueError(f"{product_type_str} is not a Product subclass")
    return product_model

def product_scorer(query: str, choice: str, score_cutoff):
    """
    Used to score product names on how closely they match a give query.
    TODO: I want to replace this eventually with a version of token_set_ratio that does not care about excessive tokens. Basically count instead of ratio
    """
    tsr = fuzz.token_set_ratio(query, choice, score_cutoff=score_cutoff)
    pr = fuzz.partial_ratio(query, choice, score_cutoff=score_cutoff)
    
    return max(tsr, pr) 

def search_products(request: HttpRequest, p_type: str):
    """
    If there is no query, return the normal search page. If there is one, return the search results of the query.
    If the product type does not match any in the db, give them a 404
    """
    product_model = load_product_model(p_type)
    
    
    query = request.GET.get("q")
    p_filter = {} # TODO: Need to update filter dict depending on filters selected in the template.
    
    products = product_model.objects.filter(**p_filter)
    p_choices = [p.product_name.lower().strip() for p in products]
    p_ids = [p.id for p in products]
    
    matches = process.extract(query, p_choices, scorer=product_scorer, limit=30)
    matched_ids = [p_ids[match[2]] for match in matches]
    matched_products = list(products.filter(id__in=matched_ids))
    matched_products.sort(key=lambda p: matched_ids.index(p.id)) # Sorts queryset by match score since querysets don't preserve order
    
    context = {
        "p_type": p_type,
        "products": matched_products,
        "query": unquote(query)
    }
    
    return render(request, "product_search.html", context)