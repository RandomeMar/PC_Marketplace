from django.contrib import admin
from .models import Listing, ListingImage

# Register your models here.
admin.site.register(ListingImage)

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "owner")
    search_fields = ("title", "owner__username")