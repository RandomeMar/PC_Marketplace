from django.db import models
from django.utils import timezone
from rapidfuzz import process, fuzz
from polymorphic.models import PolymorphicModel
from polymorphic.managers import PolymorphicQuerySet, PolymorphicManager


# Optional field types so you don't have to keep writing null=True, blank=True
class OptionalCharField(models.CharField):
    """Alternative to CharField(null=True, blank=True)."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)

class OptionalPosIntField(models.PositiveIntegerField):
    """Alternative to PositiveIntegerField(null=True, blank=True)."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)

class OptionalDecField(models.DecimalField):
    """Alternative to DecimalField(null=True, blank=True)."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('max_digits', 5)
        kwargs.setdefault('decimal_places', 2)
        super().__init__(*args, **kwargs)

class OptionalBoolField(models.BooleanField):
    """Alternative to BooleanField(null=True, blank=True)."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)


class ProductQuerySet(PolymorphicQuerySet):
    """
    Custom PolymorphicQuerySet for Product models with additional query utility.
    
    Methods:
        fuzzzy_search(query, score_cutoff=0): 
            Performs a fuzzy search on product names and returns
            a ranked list of matching Product instances.
    """
    def fuzzy_search(self, query: str, score_cutoff=60):
        """
        Performs a fuzzy search on product names.
        
        Args:
            query (str): Search string to match against product names.
            score_cutoff (int): Minimum similarity score.
        
        Returns:
            list[Product]: Ranked Products with similarity score above cutoff.
        """
        qs = self.values_list("id", "product_name")
        if qs:
            p_ids, p_choices = zip(*[(id, name.lower().strip()) for id, name in qs])
        else:
            p_ids, p_choices = ([], [])
        
        # This returns 30 best matches based on the provided query.
        # TODO: I want to replace this eventually with a version of token_set_ratio that does not care about excessive tokens. Basically count instead of ratio
        matches = process.extract(query, p_choices, scorer=lambda q, c, score_cutoff=score_cutoff: max(
                fuzz.token_set_ratio(q, c, score_cutoff=score_cutoff),
                fuzz.partial_ratio(q, c, score_cutoff=score_cutoff)
            ),
            limit=30
        )
        
        matched_ids = [p_ids[match[2]] for match in matches]
        matched_products = list(self.filter(id__in=matched_ids))
        matched_products.sort(key=lambda p: matched_ids.index(p.id)) # Sorts queryset by match score since querysets don't preserve order
        return matched_products


class ProductManager(PolymorphicManager):
    """
    Custom PolymorphicManager for Product models.
    
    Returns a ProductQuerySet instance by default. This enables the use
    of query methods like ".fuzzy_Search".
    """
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)
    
    def fuzzy_search(self, query, score_cutoff=0):
        return self.get_queryset().fuzzy_search(query, score_cutoff)



# Create your models here.
class Product(PolymorphicModel):
    """
    A Django model representing a product.
    
    This model defines common product attributes. It uses a custom
    model manager "ProductManager" that adds fuzzy search capabilities.
    
    Attributes:
        product_name (CharField): Name of the product. Required.
        manufacturer (OptionalCharField): Manufacturer's name.
        part_numbers (JSONField): List of manufacturer's part
            numbers/SKUs.
        series (OptionalCharField): The name of the product series.
        variant (OptionalCharField): The product variant.
        release_year (OptionalPosIntField): Year the product released.
        amazon_sku (OptionalCharField): Amazon product SKU.
        newegg_sku (OptionalCharField): Newegg product SKU.
        bestbuy_sku (OptionalCharField): BestBuy product SKU.
        walmart_sku (OptionalCharField): Walmart product SKU.
        adorama_sku (OptionalCharField): Adorama product SKU.
        manufacturer_url (OptionalCharField): Manufacturer URL for the
            product.
        opendb_id (UUIDField): ID for product used by opendb. Required.
        last_synced (DateTimeField): Timestamp of last opendb sync.
        base_mapping (dict): Maps model fields to fields in opendb JSON
            schema.
    """
    # id [pk]
    
    # Metadata
    product_name = models.CharField(max_length=300, verbose_name="Product Name") # REQUIRED
    manufacturer = OptionalCharField(max_length=150, verbose_name="Manufacturer")
    part_numbers = models.JSONField(default=list, verbose_name="Part Numbers") # Array of manufacturer's part numbers/SKUs
    series = OptionalCharField(max_length=150, verbose_name="Series")
    variant = OptionalCharField(max_length=150, verbose_name="Variant")
    release_year = OptionalPosIntField(verbose_name="Release Year") # TODO: Change to date
    
    # General Product Info
    amazon_sku = OptionalCharField(max_length=100)
    newegg_sku = OptionalCharField(max_length=100)
    bestbuy_sku = OptionalCharField(max_length=100)
    walmart_sku = OptionalCharField(max_length=100)
    adorama_sku = OptionalCharField(max_length=100)
    manufacturer_url = OptionalCharField(max_length=600)
    
    
    opendb_id = models.UUIDField(unique=True) # REQUIRED
    last_synced = models.DateTimeField(default=timezone.now)
    
    FILTER_FIELDS = ["manufacturer", "series", "release_year"]
    
    base_mapping = {
        "opendb_id": "opendb_id",
        "product_name": "metadata.name",
        "manufacturer": "metadata.manufacturer",
        "part_numbers": "metadata.part_numbers",
        "series": "metadata.series",
        "variant": "metadata.variant",
        "release_year": "metadata.releaseYear"
    }
    
    objects = ProductManager() # Uses custom manager so "Product.objects.filter().fuzzy_search()" is possible
    
    
    @staticmethod
    def get_val_from_path(json_dict: dict, path: str):
        """
        Retrieves a nested value from a JSON-like dictionary using a dot-delimited path.
        
        Args:
            json_dict (dict): JSON file as a nested dict.
            path (str): Dot-delimited path. (e.g., "metadata.name").
        
        Returns:
            Any | None: The value found at the path, or None if the path
                does not exist in the dict.
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
        Converts a JSON-like dict into an instance of a Product subclass.
        
        This method uses the class's "base_mapping" to map fields in the
        JSON data to fields in the model. If a record with the same
        product name already exists, it is updated.
        
        Args:
            cls (type[Product]): Product model subclass.
            json_dict (dict): JSON file as a nested dict.
        
        Returns:
            Product: Instance created from given dict.
        
        Raises:
            IntegrityError: If the dict does not provide "product_name"
                or "opendb_id".
            ValueError: If the dict does not provide the correct type
                for an attribute.
        """
        
        init_data = {}
        
        for field, path in cls.base_mapping.items():
            init_data[field] = cls.get_val_from_path(json_dict, path)
        
        product_name = init_data.pop("product_name")
        
        instance, was_created = cls.objects.update_or_create(defaults=init_data, product_name=product_name)
        
        print(f"Was created = {was_created}")
        
        return instance
    
        
        
class CPU(Product):
    """
    A subclass of Product representing CPU products specifically.
    
    Attributes:
        microarchitecture (OptionalCharField): CPU microarchitecture.
        core_family (OptionalCharField): CPU core family.
        socket (OptionalCharField): Socket type.
        cores_tot (OptionalPosIntField): Total number of physical cores.
        cores_perf (OptionalPosIntField): Number of performance cores.
        cores_eff (OptionalPosIntField): Number of efficiency cores.
        threads (OptionalPosIntField): Max number of logical threads.
        clocks_perf_base (OptionalPosIntField): Base clock speed of
            performance cores (GHz).
        clocks_perf_boost (OptionalPosIntField): Boost clock speed of
            performance cores (GHz).
        clocks_eff_base (OptionalPosIntField): Base clock speed of
            efficency cores (GHz).
        clocks_eff_boost (OptionalPosIntField): Boost clock speed of
            efficency cores (GHz).
        cache_l1 (OptionalCharField): Description of L1 cache configuration.
        cache_l2 (OptionalPosIntField): Amount of L2 cache (MB).
        cache_l3 (OptionalPosIntField): Amount of L3 cache (MB).
        tdp (OptionalPosIntField): CPU thermal design power (watts).
        intgraph_model (OptionalCharField): Integrated graphics model.
        intgraph_base_clock (OptionalPosIntField): Base clock speed of 
            integrated graphics.
        intgraph_boost_clock (OptionalPosIntField): Boost clock speed of 
            integrated graphics.
        intgraph_shader_count (OptionalPosIntField): Number of shaders
            in the integrated graphics.
        ecc_support (OptionalBoolField): Whether Error-Correcting Code
            memory is supported.
        includes_cooler (OptionalBoolField): If cooler is included.
        packaging (OptionalCharField): Packaging type.
        lithography (OptionalCharField): The manufacturing process
            technology used to make the CPU.
        simul_multithread (OptionalBoolField): If simultaneous
            multithreading is supported.
        mem_max_support (OptionalPosIntField): Max supported memory (GB).
        mem_types (JSONField): List of supported memory types.
        mem_channels (OptionalPosIntField): Max supported memory channels.
        base_mapping (dict): Maps model fields to fields in opendb JSON
            schema.
    """
    microarchitecture = OptionalCharField(max_length=100, verbose_name="Microarchitecture")
    core_family = OptionalCharField(max_length=100, verbose_name="Core Family")
    socket = OptionalCharField(max_length=50, verbose_name="Socket")
    
    # Cores
    cores_tot = OptionalPosIntField(verbose_name="Total Core Count")
    cores_perf = OptionalPosIntField(verbose_name="Performance Core Count")
    cores_eff = OptionalPosIntField(verbose_name="Efficiency Core Count")
    threads = OptionalPosIntField(verbose_name="Thread Count")
    
    # Clocks
    # Performance
    clocks_perf_base = OptionalDecField(verbose_name="Performance Core Clock")
    clocks_perf_boost = OptionalDecField(verbose_name="Performance Core Boost Clock")
    # Efficiency
    clocks_eff_base = OptionalDecField()
    clocks_eff_boost = OptionalDecField()
    
    # Cache
    cache_l1 = OptionalCharField(max_length=100, verbose_name="L1 Cache") # This explains the l1 cache structure
    cache_l2 = OptionalDecField(verbose_name="L2 Cache")
    cache_l3 = OptionalDecField(verbose_name="L3 Cache")
    
    tdp = OptionalPosIntField(verbose_name="TDP")
    
    # Integrated Graphics
    intgraph_model = OptionalCharField(max_length=100, verbose_name="Integrated Graphics") # The model of integrated graphics
    intgraph_base_clock = OptionalDecField()
    intgraph_boost_clock = OptionalDecField()
    intgraph_shader_count = OptionalDecField()
    
    ecc_support = OptionalBoolField(verbose_name="ECC Support") # Whether the CPU supports Error-Correcting Code memory
    
    includes_cooler = OptionalBoolField(verbose_name="Includes Cooler")
    
    packaging = OptionalCharField(max_length=100, verbose_name="Packaging") # Describes type of packaging
    
    lithography = OptionalCharField(max_length=50, verbose_name="Lithography") # The manufacturing process technology used. Can be multiple process technologies if chiplet design
    
    simul_multithread = OptionalBoolField(verbose_name="Simultaneous Multithreading")
    
    # Memory
    mem_max_support = OptionalDecField() # In GB
    mem_types = models.JSONField(default=list)
    mem_channels = OptionalPosIntField()
    
    FILTER_FIELDS = Product.FILTER_FIELDS + [
        "microarchitecture", "core_family", "socket", "cores_tot",
        "threads", "clocks_perf_base", "clocks_perf_boost", "tdp",
        "intgraph_model", "ecc_support", "includes_cooler", "simul_multithread"
        ]
    
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
    
    class Meta:
        db_table = ''
        managed = True
        verbose_name = 'CPU'
        verbose_name_plural = 'CPUs'
