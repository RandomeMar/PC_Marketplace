from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.apps import apps
from products.models import Product, ProductQuerySet
from urllib.parse import unquote

# Create your views here.


def test(request: HttpRequest):
    return HttpResponse("TESTING")

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
