from django.apps import apps
from git import Repo
import os
import json
import models

def import_from_opendb(product_model_name: str):
    """
    Imports data base entries for the product type specified from the buildcores opendb.
    """
    MODEL_TO_DIR_MAPPING = {
        models.CPU: "CPU",
    }
    
    BUILDCORES_REPO = "https://github.com/buildcores/buildcores-open-db"
    LOCAL_PATH = "./buildcores-open-db"
    
    product_class = apps.get_model("products", product_model_name)
    if product_class == None:
        raise ValueError(f"Model {product_model_name} not found in products.")
    
    if not os.path.isdir(LOCAL_PATH):
        Repo.clone_from(BUILDCORES_REPO, LOCAL_PATH)
        print("Repository cloned")
    
    directory = f"{LOCAL_PATH}/open-db/{MODEL_TO_DIR_MAPPING[product_class]}"
    
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        with open(item_path, 'r') as f:
            item_data = json.load(f)
        item_instance = product_class.dict_to_model(item_data)
        print(item_instance.product_name)
    
    
    