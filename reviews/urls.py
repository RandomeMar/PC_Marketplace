from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("<int:l_id>/create/", views.add_review, name="add_review"),
    path("<int:r_id>/edit/", views.edit_review, name="edit_review"),
    path("<int:r_id>/delete/", views.delete_review, name="delete_review"),
]  