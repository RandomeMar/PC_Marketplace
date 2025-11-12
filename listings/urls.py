from django.urls import path
from . import views

app_name = "listings"

urlpatterns = [
    # TODO: Figure this shit out
    # marketplace views (MAIN)
    
    
    
    # path('view/<int:l_id>/', views.load_listing_page, name='load_listing_page'), # NOTE: Overrides "l_id/"
    # path('<int:l_id>/', views.load_listing_page, name='load_listing_page_short'), # NOTE: Overrides "l_id/"

    # path('select-type/', views.select_p_type, name='select_p_type'), # Select p_type NOTE: Overrides ""
    # path('create/', views.create_listing, name='create_listing'), # Create listing for product of p_type NOTE: Overrides "p_type/p_id/create"
    
    
    
    # NEW:
    path('', views.all_listings_page, name='all_listings_page'),  # Browse all listings
    
    path('my-listings/', views.my_listings, name='my_listings'),  # View user's listings
    path('edit/<int:l_id>/', views.edit_listing, name='edit_listing'), # Edit a listing
    #path('delete/<int:l_id>/', views.delete_listing, name='delete_listing'),  # Delete a listing (NOT IMPLEMENTED YET)
    #path('filter/<str:p_type>/', views.filter_by_type, name='filter_by_type'), # Filter listings by product type (NOT IMPLEMENTED YET)
    
    
    # OLD:
    path("test/", views.test, name="test"), # Test view
    
    path("", views.select_p_type, name="select_p_type"), # For selecting a product type for searching
    path("<str:p_type>/search/", views.search_listings, name="search_listings"), # Handles searching for listings of a specified product type
    
    path("new/", views.select_p_type, {"next_url": "search-products/"}, name="select_p_type_new"), # For selecting a product type when making a new listing
    path("<str:p_type>/search-products/", views.search_products, name="search_products"), # For searching for a product to make a new listing from
    path("<str:p_type>/<int:p_id>/create/", views.create_listing, name="create_listing"), # Handles form for listing creation
    
    path("<int:l_id>/", views.load_listing_page, name="load_listing_page"), # Loads a listing detail page
]