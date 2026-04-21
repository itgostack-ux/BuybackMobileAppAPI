from repositories.item_repository import *


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

def get_brands_by_subcategory_service(
    item_group_id=None,
    category_id=None,
    sub_category_id=None
):
    return response(
        get_brands_by_subcategory_repo(
            item_group_id,
            category_id,
            sub_category_id
        )
    )
def get_models_filtered_service(
    item_group_id=None,
    category_id=None,
    sub_category_id=None,
    brand_id=None
):
    return response(
        get_models_filtered_repo(
            item_group_id,
            category_id,
            sub_category_id,
            brand_id
        )
    )

def get_model_distinct_attributes_service(model_id):
    return response(get_model_distinct_attributes_repo(model_id))

def get_attribute_values_service(model_id, spec):
    return response(get_attribute_values_repo(model_id, spec))

def get_items_service(
    item_group_id,
    category_id,
    sub_category_id,
    brand_id,
    model_id,
    filters
):
    return response(
        get_items_repo(
            item_group_id,
            category_id,
            sub_category_id,
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