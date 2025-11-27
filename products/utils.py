from django.apps import apps
from git import Repo
import os
import json
from . import models

def import_from_opendb(product_model_name: str) -> None:
    """
    Imports product records from Buildcores opendb to local database.
    
    Given the name of a Product subclass, this function ensures a local
    opendb repository exists (cloning if not), then iterates over all
    json files in the specified product directory. Each json file is
    converted into an instance of the Product subclass.
    
    Args:
        product_model_name (str): Name of a subclass of Product.
    
    Returns:
        None
    
    Raises:
        ValueError: If "product_model_name" is not a subclass of Product.
        KeyError: If the model exists but there is no mapping in
            "MODEL_TO_DIR_MAPPING".
    """
    MODEL_TO_DIR_MAPPING = {
        models.CPU: "CPU",
        models.GPU: "GPU",
        models.Motherboard: "Motherboard",
        models.PCCase: "PCCase",
        models.PSU: "PSU",
        models.RAM: "RAM",
        models.Storage: "Storage",
    }
    
    BUILDCORES_REPO = "https://github.com/buildcores/buildcores-open-db"
    LOCAL_PATH = "./buildcores-open-db"
    
    product_class: type[models.Product] = apps.get_model("products",
        product_model_name)
    if product_class == None:
        raise ValueError(f"Model {product_model_name} not found in products.")
    
    if not os.path.isdir(LOCAL_PATH):
        Repo.clone_from(BUILDCORES_REPO, LOCAL_PATH)
        print("Repository cloned")
    
    directory = f"{LOCAL_PATH}/open-db/{product_model_name}"
    
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        with open(item_path, 'r', encoding="utf-8") as f:
            item_data = json.load(f)
        item_instance = product_class.dict_to_model(item_data)
        
    
    print("FINISHED IMPORT_FROM_OPEN_DB")
    
    
    