from django.db import models
from django.utils import timezone


# Optional field types so you don't have to keep writing null=True, blank=True
class OptionalCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)

class OptionalPosIntField(models.PositiveIntegerField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)

class OptionalBoolField(models.BooleanField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)




# Create your models here.
class Product(models.Model):
    # id [pk]
    
    # Metadata
    product_name = models.CharField(max_length=300) # REQUIRED
    manufacturer = OptionalCharField(max_length=150)
    part_numbers = models.JSONField(default=list) # Array of manufacturer's part numbers/SKUs
    series = OptionalCharField(max_length=150)
    variant = OptionalCharField(max_length=150)
    release_year = OptionalPosIntField()
    
    # General Product Info
    amazon_sku = OptionalCharField(max_length=100)
    newegg_sku = OptionalCharField(max_length=100)
    bestbuy_sku = OptionalCharField(max_length=100)
    walmart_sku = OptionalCharField(max_length=100)
    adorama_sku = OptionalCharField(max_length=100)
    manufacturer_url = OptionalCharField(max_length=600)
    
    
    opendb_id = models.UUIDField(unique=True) # REQUIRED
    last_synced = models.DateTimeField(default=timezone.now)
    
    base_mapping = {
        "opendb_id": "opendb_id",
        "product_name": "metadata.name",
        "manufacturer": "metadata.manufacturer",
        "part_numbers": "metadata.part_numbers",
        "series": "metadata.series",
        "variant": "metadata.variant",
        "release_year": "metadata.releaseYear"
    }
    
    
    @staticmethod
    def get_val_from_path(json_dict: dict, path: str):
        """
        Goes through paths defined in the base_mapping to see if an attribute was specified
        """
        result = json_dict
        keys = path.split('.')
        for key in keys:
            if not isinstance(result, dict):
                return None
            result = result.get(key)
        return result
    
    @classmethod
    def dict_to_model(cls, json_dict: dict):
        """
        Converts dictionary into a model instance
        """
        
        init_data = {}
        
        for field, path in cls.base_mapping.items():
            init_data[field] = cls.get_val_from_path(json_dict, path)
        
        product_name = init_data.pop("product_name")
        
        instance, was_created = cls.objects.update_or_create(defaults=init_data, product_name=product_name)
        
        print(f"Was created = {was_created}")
        
        return instance
    
        
        
class CPU(Product):
    microarchitecture = OptionalCharField(max_length=100)
    core_family = OptionalCharField(max_length=100)
    socket = OptionalCharField(max_length=50)
    
    # Cores
    cores_tot = OptionalPosIntField()
    cores_perf = OptionalPosIntField()
    cores_eff = OptionalPosIntField()
    threads = OptionalPosIntField()
    
    # Clocks
    # Performance
    clocks_perf_base = OptionalPosIntField()
    clocks_perf_boost = OptionalPosIntField()
    # Efficiency
    clocks_eff_base = OptionalPosIntField()
    clocks_eff_boost = OptionalPosIntField()
    
    # Cache
    cache_l1 = OptionalCharField(max_length=100) # This explains the l1 cache structure
    cache_l2 = OptionalPosIntField()
    cache_l3 = OptionalPosIntField()
    
    tdp = OptionalPosIntField()
    
    # Integrated Graphics
    intgraph_model = OptionalCharField(max_length=100) # The model of integrated graphics
    intgraph_base_clock = OptionalPosIntField()
    intgraph_boost_clock = OptionalPosIntField()
    intgraph_shader_count = OptionalPosIntField()
    
    ecc_support = OptionalBoolField() # Whether the CPU supports Error-Correcting Code memory
    
    includes_cooler = OptionalBoolField()
    
    packaging = OptionalCharField(max_length=100) # Describes type of packaging
    
    lithography = OptionalCharField(max_length=50) # The manufacturing process technology used. Can be multiple process technologies if chiplet design
    
    simul_multithread = OptionalBoolField()
    
    # Memory
    mem_max_support = OptionalPosIntField() # In GB
    mem_types = models.JSONField(default=list)
    mem_channels = OptionalPosIntField()
    
    
    base_mapping = Product.base_mapping.copy()
    base_mapping |= {
        "microarchitecture": "microarchitecture",
        "core_family": "coreFamily",
        "socket": "socket",
        
        # Cores
        "cores_tot": "cores.total",
        "cores_perf": "cores.performance",
        "cores_eff": "cores.efficiency",
        "threads": "cores.threads",
        
        # Clocks
        "clocks_perf_base": "clocks.performance.base",
        "clocks_perf_boost": "clocks.performance.boost",
        "clocks_eff_base": "clocks.efficiency.base",
        "clocks_eff_boost": "clocks.efficiency.boost",
        
        # Cache
        "cache_l1": "cache.l1",
        "cache_l2": "cache.l2",
        "cache_l3": "cache.l3",
        
        # Power
        "tdp": "specifications.tdp",
        
        # Integrated Graphics
        "intgraph_model": "specifications.integratedGraphics.model",
        "intgraph_base_clock": "specifications.integratedGraphics.baseClock",
        "intgraph_boost_clock": "specifications.integratedGraphics.boostClock",
        "intgraph_shader_count": "specifications.integratedGraphics.shaderCount",
        
        # Features
        "ecc_support": "specifications.eccSupport",
        "includes_cooler": "specifications.includesCooler",
        
        # Packaging & lithography
        "packaging": "specifications.packaging",
        "lithography": "specifications.lithography",
        
        # Multithreading
        "simul_multithread": "specifications.simultaneousMultithreading",
        
        # Memory
        "mem_max_support": "specifications.memory.maxSupport",
        "mem_types": "specifications.memory.types",
        "mem_channels": "specifications.memory.channels"
    }
    
