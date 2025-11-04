from django.urls import path
from . import views

app_name = "listings"

urlpatterns = [
    
    # Searching for listings
    path("test/", views.test, name="test"),
    # "listings/", # Select p_type
    # "listings/<p_type>/search", # Searches for listings of p_type
    
    # Create listings
    # "listings/new/", # Select p_type of new product
    path("<str:p_type>/search-products/", views.search_products, name="search_products"), # Search for product of type p_type
    # "listings/<p_type>/<p_id>/new/", # Form for new listing
    
    # Listing page
    # "listings/<l_id>/",
]