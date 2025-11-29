from django.db import models, utils
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

class OptionalFloatField(models.FloatField):
    """Alternative to DecimalField(blank=True)."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)

class OptionalBoolField(models.BooleanField):
    """Alternative to BooleanField(null=True, blank=True)."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)


# Create your models here.
class Product(PolymorphicModel):
    """
    A Django model representing a product.
    
    This model will never directly be used. Instead, its subclasses will
    inherit from it.
    
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
            value = cls.get_val_from_path(json_dict, path)
            internal_type = cls._meta.get_field(field).get_internal_type()
            init_data[field] = value
            
        product_name = init_data.pop("product_name")


        # instance, was_created = cls.objects.update_or_create(defaults=init_data, product_name=product_name)
        # print(f"Was created = {was_created}")
        # return instance

        try:
            instance, was_created = cls.objects.update_or_create(defaults=init_data, product_name=product_name)
        
            print(f"Was created = {was_created}")
            return instance
        except utils.IntegrityError:
            print(f"product_name: {product_name}")
            for key, value in init_data.items():
                print(f"{key}: {value}")
        
    
    def __str__(self):
        return f"{self.product_name}"
    
        
        
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
    clocks_perf_base = OptionalFloatField(verbose_name="Performance Core Clock")
    clocks_perf_boost = OptionalFloatField(verbose_name="Performance Core Boost Clock")
    # Efficiency
    clocks_eff_base = OptionalFloatField()
    clocks_eff_boost = OptionalFloatField()
    
    # Cache
    cache_l1 = OptionalCharField(max_length=100, verbose_name="L1 Cache") # This explains the l1 cache structure
    cache_l2 = OptionalFloatField(verbose_name="L2 Cache")
    cache_l3 = OptionalFloatField(verbose_name="L3 Cache")
    
    tdp = OptionalPosIntField(verbose_name="TDP")
    
    # Integrated Graphics
    intgraph_model = OptionalCharField(max_length=100, verbose_name="Integrated Graphics") # The model of integrated graphics
    intgraph_base_clock = OptionalFloatField()
    intgraph_boost_clock = OptionalFloatField()
    intgraph_shader_count = OptionalFloatField()
    
    ecc_support = OptionalBoolField(verbose_name="ECC Support") # Whether the CPU supports Error-Correcting Code memory
    
    includes_cooler = OptionalBoolField(verbose_name="Includes Cooler")
    
    packaging = OptionalCharField(max_length=100, verbose_name="Packaging") # Describes type of packaging
    
    lithography = OptionalCharField(max_length=50, verbose_name="Lithography") # The manufacturing process technology used. Can be multiple process technologies if chiplet design
    
    simul_multithread = OptionalBoolField(verbose_name="Simultaneous Multithreading")
    
    # Memory
    mem_max_support = OptionalFloatField() # In GB
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
        verbose_name = 'CPU'
        verbose_name_plural = 'CPUs'


class GPU(Product):
    chipset_manufacturer = OptionalCharField(max_length=100)
    chipset = OptionalCharField(max_length=100, verbose_name="Chipset")

    memory = OptionalFloatField(verbose_name="Memory")
    memory_type = OptionalCharField(max_length=100, verbose_name="Memory Type")

    core_base_clock = OptionalFloatField()
    core_boost_clock = OptionalFloatField()
    core_count = OptionalPosIntField()
    effective_memory_clock = OptionalFloatField()
    memory_bus = OptionalPosIntField()

    interface = OptionalCharField(max_length=100, verbose_name="Interface")

    color = models.JSONField(default=list)

    frame_sync = OptionalCharField(max_length=100, verbose_name="Frame Sync")

    length = OptionalFloatField(verbose_name="Length")

    tdp = OptionalPosIntField(verbose_name="TDP")

    case_expansion_slot_width = OptionalFloatField()

    total_slot_width = OptionalFloatField()

    cooling = OptionalCharField(max_length=100)

    pcie_6_pin = OptionalPosIntField()
    pcie_8_pin = OptionalPosIntField()
    pcie_12VHPWR = OptionalPosIntField()
    pcie_12V_2x6 = OptionalPosIntField()

    hdmi_2_2 = OptionalPosIntField()
    hdmi_2_1 = OptionalPosIntField()
    hdmi_2_0 = OptionalPosIntField()
    displayport_2_1 = OptionalPosIntField()
    displayport_2_1a = OptionalPosIntField()
    displayport_1_4a = OptionalPosIntField()
    displayport_2_1_b = OptionalPosIntField()
    dvi_d = OptionalPosIntField()
    vga = OptionalPosIntField()




    FILTER_FIELDS = Product.FILTER_FIELDS + [
        "chipset", "memory", "memory_type", "interface", "frame_sync", "length", "tdp"
    ]

    base_mapping = Product.base_mapping.copy()
    base_mapping |= {
        "chipset_manufacturer": "chipset_manufacturer",
        "chipset": "chipset",

        "memory": "memory",
        "memory_type": "memory_type",

        "core_base_clock": "core_base_clock",
        "core_boost_clock": "core_boost_clock",
        "core_count": "core_count",
        "effective_memory_clock": "effective_memory_clock",
        "memory_bus": "memory_bus",

        "interface": "interface",

        "color": "color",

        "frame_sync": "frame_sync",

        "length": "length",

        "tdp": "tdp",

        "case_expansion_slot_width": "case_expansion_slot_width",

        "total_slot_width": "total_slot_width",

        "cooling": "cooling",

        "pcie_6_pin": "power_connectors.pcie_6_pin",
        "pcie_8_pin": "power_connectors.pcie_8_pin",
        "pcie_12VHPWR": "power_connectors.pcie_12VHPWR",
        "pcie_12V_2x6": "power_connectors.pcie_12V_2x6",

        "hdmi_2_2": "video_outputs.hdmi_2_2",
        "hdmi_2_1": "video_outputs.hdmi_2_1",
        "hdmi_2_0": "video_outputs.hdmi_2_0",
        "displayport_2_1": "video_outputs.displayport_2_1",
        "displayport_2_1a": "video_outputs.displayport_2_1a",
        "displayport_1_4a": "video_outputs.displayport_1_4a",
        "displayport_2_1_b": "video_outputs.displayport_2_1_b",
        "dvi_d": "video_outputs.dvi_d",
        "vga": "video_outputs.vga",
    }
    class Meta:
        verbose_name = 'GPU'
        verbose_name_plural = 'GPUs'


class Motherboard(Product):
    socket = OptionalCharField(max_length=100, verbose_name="Socket")
    form_factor = OptionalCharField(max_length=100, verbose_name="Form Factor")
    chipset = OptionalCharField(max_length=100, verbose_name="Chipset")
    memory_max = OptionalFloatField()
    memory_ram_type = OptionalCharField(max_length=100, verbose_name="RAM Type")
    memory_slots = OptionalPosIntField(verbose_name="RAM Slots")

    color = models.JSONField(default=list, null=True)

    pcie_slots = models.JSONField(default=list, null=True)
    m2_slots = models.JSONField(default=list, null=True)

    sata_6_gb_s = OptionalPosIntField()
    sata_3_gb_s = OptionalPosIntField()
    u2 = OptionalPosIntField()

    onboard_ethernets = models.JSONField(default=list, null=True)

    wireless_networking = OptionalCharField(max_length=100)

    usb_2_0 = OptionalPosIntField()
    usb_3_2_gen_1 = OptionalPosIntField()
    usb_3_2_gen_2 = OptionalPosIntField()
    usb_3_2_gen_2x2 = OptionalPosIntField()
    usb_4 = OptionalPosIntField()
    usb_4_80g = OptionalPosIntField()

    cpu_fan = OptionalPosIntField()
    case_fan = OptionalPosIntField()
    pump = OptionalPosIntField()
    cpu_opt = OptionalPosIntField()

    argb_5v = OptionalPosIntField()
    rgb_12v = OptionalPosIntField()

    FILTER_FIELDS = Product.FILTER_FIELDS + [
        "socket", "form_factor", "chipset", "memory_ram_type",
        "memory_slots", "wireless_networking",
    ]

    base_mapping = Product.base_mapping.copy()
    base_mapping |= {
        "socket": "socket",
        "form_factor": "form_factor",
        "chipset": "chipset",

        "memory_max": "memory.max",
        "memory_ram_type": "memory.ram_type",
        "memory_slots": "memory.slots",

        "color": "color",

        "pcie_slots": "pcie_slots",
        "m2_slots": "m2_slots",

        "sata_6_gb_s": "storage_devices.sata_6_gb_s",
        "sata_3_gb_s": "storage_devices.sata_3_gb_s",
        "u2": "storage_devices.u2",

        "onboard_ethernets": "onboard_ethernets",

        "wireless_networking": "wireless_networking",

        "usb_2_0": "usb_headers.usb_2_0",
        "usb_3_2_gen_1": "usb_headers.usb_3_2_gen_1",
        "usb_3_2_gen_2": "usb_headers.usb_3_2_gen_2",
        "usb_3_2_gen_2x2": "usb_headers.usb_3_2_gen_2x2",
        "usb_4": "usb_headers.usb_4",
        "usb_4_80g": "usb_headers.usb_4_80g",

        "cpu_fan": "fan_headers.cpu_fan",
        "case_fan": "fan_headers.case_fan",
        "pump": "fan_headers.pump",
        "cpu_opt": "fan_headers.cpu_opt",

        "argb_5v": "rgb_headers.argb_5v",
        "rgb_12v": "rgb_headers.rgb_12v",

    }
    class Meta:
        verbose_name = "Motherboard"
        verbose_name_plural = "Motherboards"


class PCCase(Product):
    FILTER_FIELDS = Product.FILTER_FIELDS + [

    ]

    base_mapping = Product.base_mapping.copy()
    base_mapping |= {

    }
    class Meta:
        verbose_name = "PC Case"
        verbose_name_plural = "PC Cases (Not implemented)"


class PSU(Product):
    FILTER_FIELDS = Product.FILTER_FIELDS + [

    ]

    base_mapping = Product.base_mapping.copy()
    base_mapping |= {

    }
    class Meta:
        verbose_name = "Power Supply"
        verbose_name_plural = "Power Supplies (Not implemented)"


class RAM(Product):
    FILTER_FIELDS = Product.FILTER_FIELDS + [

    ]

    base_mapping = Product.base_mapping.copy()
    base_mapping |= {

    }
    class Meta:
        verbose_name = 'RAM'
        verbose_name_plural = 'RAM (Not implemented)'


class Storage(Product):
    FILTER_FIELDS = Product.FILTER_FIELDS + [

    ]

    base_mapping = Product.base_mapping.copy()
    base_mapping |= {

    }
    class Meta:
        verbose_name = 'Storage'
        verbose_name_plural = 'Storage (Not implemented)'