from django.urls import path
from . import views

app_name = "listings"

urlpatterns = [
    # marketplace views (MAIN)
    path('', views.listing_page, name='listing_page'),  # Browse all listings
    path('view/<int:l_id>/', views.load_listing_page, name='load_listing_page'),
    path('<int:l_id>/', views.load_listing_page, name='load_listing_page_short'),

    path('select-type/', views.select_p_type, name='select_p_type'), # Select p_type
    path("new/", views.select_p_type, {"next_url": "search-products/"}, name="select_p_type_new"), # Select p_type of new product
    path("<str:p_type>/search-products/", views.search_products, name="search_products"), # Search for product of type p_type

    path('create/', views.create_listing, name='create_listing'), # Create listing for product of p_type
    
    
    path('my-listings/', views.my_listings, name='my_listings'),  # View user's listings
    path('edit/<int:l_id>/', views.edit_listing, name='edit_listing'), # Edit a listing
    #path('delete/<int:l_id>/', views.delete_listing, name='delete_listing'),  # Delete a listing (NOT IMPLEMENTED YET)
    #path('filter/<str:p_type>/', views.filter_by_type, name='filter_by_type'), # Filter listings by product type (NOT IMPLEMENTED YET)
]