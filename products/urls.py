from django.urls import path
from . import views

urlpatterns = [
    path("<str:p_type>/", views.search_products, name="search_products")
]