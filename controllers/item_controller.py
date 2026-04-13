from services.item_service import *


def get_device_items_controller():
    return get_device_items_service()


def get_categories_controller(item_group_id):
    return get_categories_service(item_group_id)


def get_sub_categories_controller(category_id=None,item_group_id=None):
    return get_sub_categories_service(category_id,item_group_id)


def get_manufacturers_controller():
    return get_manufacturers_service()


def get_brands_controller(manufacturer=None):
    return get_brands_service(manufacturer)


def get_models_controller(brand_id=None):
    return get_models_service(brand_id)


def get_attributes_controller():
    return get_attributes_service()


def get_model_spec_values_controller(model_id=None):
    return get_model_spec_values_service(model_id)


def get_model_with_spec_controller(model_id=None):
    return get_model_with_spec_service(model_id)


def get_items_controller(params):
    return get_items_service(params)

def get_brands_by_subcategory_controller(
    item_group_id=None,
    category_id=None,
    sub_category_id=None
):
    return get_brands_by_subcategory_service(
        item_group_id,
        category_id,
        sub_category_id
    )

def get_models_filtered_controller(
    item_group_id=None,
    category_id=None,
    sub_category_id=None,
    brand_id=None
):
    return get_models_filtered_service(
        item_group_id,
        category_id,
        sub_category_id,
        brand_id
    )
def get_model_distinct_attributes_controller(model_id):
    return get_model_distinct_attributes_service(model_id)

def get_attribute_values_controller(model_id, spec):
    return get_attribute_values_service(model_id, spec)

def get_items_controller(
    item_group_id,
    category_id,
    sub_category_id,
    brand_id,
    model_id,
    filters
):
    return get_items_service(
        item_group_id,
        category_id,
        sub_category_id,
        brand_id,
        model_id,
        filters
    )

def get_colors_by_storage_controller(model_id: int, storage_value: str):
    return get_colors_by_storage_service(model_id, storage_value)

def get_buyback_price_controller(item_code):
    return get_buyback_price_service(item_code)