from django.contrib import admin
from .models import Listing, ListingImage, Purchase, Message

# Register your models here.
admin.site.register(ListingImage)

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "owner")
    search_fields = ("title", "owner__username")

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("listing", "seller", "buyer", "status")
    search_fields = ("is_flagged",)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "listing", "timestamp")
    search_fields = ("message_text",)