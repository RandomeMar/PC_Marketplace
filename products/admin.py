from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin
from .models import Product, CPU, GPU
from .utils import import_from_opendb

# Register your models here.
@admin.register(Product)
class ProductAdmin(PolymorphicParentModelAdmin):
    base_model = Product
    child_models = [CPU]
    list_display = ["product_name", "id", "opendb_id", "last_synced"]

class ProductChildAdmin(PolymorphicChildModelAdmin):
    base_model: type[Product]
    list_display = ProductAdmin.list_display
    actions = ["sync_with_opendb"]
    
    def sync_with_opendb(self, request, qs):
        import_from_opendb(self.base_model.__name__)


@admin.register(CPU)
class CPUAdmin(ProductChildAdmin):
    base_model = CPU

@admin.register(GPU)
class GPUAdmin(ProductChildAdmin):
    base_model = GPU