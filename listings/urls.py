from django.urls import path
from . import views

app_name = "listings"

urlpatterns = [
    path("test/", views.test, name="test"),

    
    path("", views.select_p_type, name="select_p_type"), # Select p_type
    path("<str:p_type>/search/", views.search_listings, name="search_listings"), # Searches for listings of p_type
    
    path("new/", views.select_p_type, {"next_url": "search-products/"}, name="select_p_type_new"), # Select p_type of new product
    path("<str:p_type>/search-products/", views.search_products, name="search_products"), # Search for product of type p_type
    path("<str:p_type>/<int:p_id>/new/", views.create_listing, name="create_listing"), # Form for new listing
    
    path("<int:l_id>/", views.load_listing_page, name="load_listing_page"), # Load a listing page
]