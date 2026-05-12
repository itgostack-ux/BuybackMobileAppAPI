from repositories.item_repository import *
import re


def response(data):
    return {"success":True,"count":len(data),"data":data}


def get_device_items_service():
    return response(get_device_items_repo())


def get_categories_service(item_group_id):
    return response(get_categories_repo(item_group_id))


def get_sub_categories_service(category_id=None,item_group_id=None):
    return response(get_sub_categories_repo(category_id,item_group_id))


def get_model_with_spec_service(model_id=None):
    return response(get_model_with_spec_repo(model_id))

def get_brands_by_subcategory_service(item_group_id=None):
    return response(
        get_brands_by_subcategory_repo(item_group_id)
    )


    
def get_models_filtered_service(
    item_group_id=None,
    brand_id=None
):
    return response(
        get_models_filtered_repo(
            item_group_id,
            brand_id
        )
    )
def get_model_distinct_attributes_service(model_id):
    return response(get_model_distinct_attributes_repo(model_id))

def get_attribute_values_service(model_id, spec):
    return response(get_attribute_values_repo(model_id, spec))

def get_items_service(
    item_group_id,
    brand_id,
    model_id,
    filters
):
    return response(
        get_items_repo(
            item_group_id,
            brand_id,
            model_id,
            filters
        )
    )


def get_colors_by_storage_service(model_id: int, storage_value: str):
    data = get_colors_by_storage_repo(model_id, storage_value)

    return {
        "success": True,
        "message": "Color list fetched successfully",
        "data": data
    }

def get_buyback_price_service(item_code):
    return response(get_buyback_price_repo(item_code))


import re

def parse_device_string(device_string):

    text = (device_string or "").lower().strip()

    gb_values = re.findall(
        r'(\d+\s?(?:gb|tb))',
        text,
        re.IGNORECASE
    )

    cleaned_values = []

    for value in gb_values:

        cleaned_value = value.replace(
            " ",
            ""
        ).lower()

        cleaned_values.append(cleaned_value)

    ram = None
    storage = None

    if len(cleaned_values) >= 2:

        ram = cleaned_values[0]
        storage = cleaned_values[1]

    elif len(cleaned_values) == 1:

        storage = cleaned_values[0]

    # -----------------------------------
    # Remove GB/TB values safely
    # -----------------------------------
    model_name = re.sub(
        r'\d+\s?(gb|tb)',
        '',
        text,
        flags=re.IGNORECASE
    )

    model_name = model_name.replace("-", " ")
    model_name = model_name.replace("_", " ")

    model_name = " ".join(
        model_name.split()
    )

    return {
        "model_name": model_name,
        "ram": ram,
        "storage": storage
    }

# ---------------------------------------------------
# DEVICE VARIANTS SERVICE
# ---------------------------------------------------

def get_device_variants_service(device_name):

    parsed = parse_device_string(
        device_name
    )

    data = get_variants_by_model_storage_repo(
        device_name
    )

    return {
        "success": True,
        "device_name": device_name,
        "model_name": parsed["model_name"],
        "ram": parsed["ram"],
        "storage": parsed["storage"],
        "count": len(data),
        "variants": data
    }