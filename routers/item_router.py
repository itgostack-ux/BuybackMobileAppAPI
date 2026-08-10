from fastapi import APIRouter,Query
from controllers.item_controller import *
router=APIRouter(prefix="/api/v1",tags=["Items"])


@router.get("/GetBrands")
def get_brands(
    item_group_id: int | None = None,
):
    return get_brands_by_subcategory_controller(
        item_group_id
    )


@router.get("/GetModelsByBrand")
def get_models_by_filter(
    item_group_id: int | None = None,
    brand_id: int | None = None
):
    return get_models_filtered_controller(
        item_group_id,
        brand_id
    )

@router.get("/GetModelByStorage")
def get_attribute_values(
    model_id: int
    ):
    return get_attribute_values_controller(model_id)

@router.get("/GetColorsByStorage")
def get_colors_by_storage(
    model_id: int = Query(...),
    ram_storage: str = Query(..., description="Format: RAM/Storage (e.g. 4GB/64GB), or just Storage for storage-only phones (e.g. 128GB)")
):
    return get_colors_by_storage_controller(model_id, ram_storage)

@router.get("/GetItemsWithSpec")
def get_items(
    item_group_id: int = Query(...),
    brand_id: int = Query(...),
    model_id: int = Query(...),
    filters: str = Query(
        ...,
        description='JSON object of spec:value pairs (e.g. {"Storage":"128GB","Colour":"Black"}) '
                    'or shorthand "RAM/Storage/Colour" (e.g. "4GB/64GB/Black")'
    )
):
    return get_items_controller(
        item_group_id,
        brand_id,
        model_id,
        filters
    )

@router.get("/GetBuybackPrice")
def get_buyback_price(item_code: str = Query(...)):
    return get_buyback_price_controller(item_code)