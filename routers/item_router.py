from fastapi import APIRouter,Query
from controllers.item_controller import *

router=APIRouter(prefix="/api/v1",tags=["Items"])


@router.get("/GetDeviceItems")
def get_device_items():
    return get_device_items_controller()


@router.get("/GetCategories")
def get_categories(item_group_id:int=Query(...)):
    return get_categories_controller(item_group_id)


@router.get("/GetSubCategories")
def get_sub_categories(category_id:int|None=None,item_group_id:int|None=None):
    return get_sub_categories_controller(category_id,item_group_id)


@router.get("/GetManufacturers")
def get_manufacturers():
    return get_manufacturers_controller()


@router.get("/GetManufacturerByBrands")
def get_brands(manufacturer:str|None=None):
    return get_brands_controller(manufacturer)


@router.get("/GetBrands")
def get_brands_all():
    return get_brands_controller()


@router.get("/GetModels")
def get_models(brand_id:int|None=None):
    return get_models_controller(brand_id)


@router.get("/GetAttributes")
def get_attributes():
    return get_attributes_controller()


@router.get("/GetModelSpecValues")
def get_model_spec_values(model_id:int|None=None):
    return get_model_spec_values_controller(model_id)


@router.get("/GetModelWithSpecification")
def get_model_with_spec(model_id:int|None=None):
    return get_model_with_spec_controller(model_id)


@router.get("/GetItems")
def get_items(item_group_id:int,
              category_id:int,
              sub_category_id:int,
              brand_id:int,
              model_id:int,
              spec:str,
              spec_value:str):

    params=(item_group_id,category_id,sub_category_id,
            brand_id,model_id,spec,spec_value)

    return get_items_controller(params)