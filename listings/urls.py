from django.urls import path
from . import views

app_name = "listings"

urlpatterns = [
    path("test/", views.test, name="test"), # Test view
    path('', views.all_listings_page, name='all_listings_page'),  # Browse all listings
    
    # Searching for listings
    path("types/", views.select_p_type, name="select_p_type"), # 1. Select a product type.
    path("<str:p_type>/search/", views.search_listings, name="search_listings"), # 2. Search for a listing.
    
    # For creating listings
    path("new/", views.select_p_type, {"next_url": "search-products/"}, name="select_p_type_new"), # 1. Select a product type.
    path("<str:p_type>/search-products/", views.search_products, name="search_products"), # 2. Search for a product in that product type you want to sell.
    path("<str:p_type>/<int:p_id>/create/", views.create_listing, name="create_listing"), # 3. Fill out listing specific data in a form
    
    # Other listing operations
    path('my-listings/', views.my_listings, name='my_listings'),  # If signed in, look at all of your listings.
    path('edit/<int:l_id>/', views.edit_listing, name='edit_listing'), # Edit a listing.
    #path('delete/<int:l_id>/', views.delete_listing, name='delete_listing'),  # Delete a listing (NOT IMPLEMENTED YET)
    #path('filter/<str:p_type>/', views.filter_by_type, name='filter_by_type'), # Filter listings by product type (NOT IMPLEMENTED YET)
    
    # Loads listing detail page
    path("<int:l_id>/", views.load_listing_detail, name="load_listing_detail"),
]  
"""
OLD:

path('view/<int:l_id>/', views.load_listing_page, name='load_listing_page'), # NOTE: Overrides "l_id/"
path('<int:l_id>/', views.load_listing_page, name='load_listing_page_short'), # NOTE: Overrides "l_id/"

path('select-type/', views.select_p_type, name='select_p_type'), # Select p_type NOTE: Overrides ""
path('create/', views.create_listing, name='create_listing'), # Create listing for product of p_type NOTE: Overrides "p_type/p_id/create"
"""
