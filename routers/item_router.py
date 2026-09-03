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
    storage: str = Query(..., description="Storage value, e.g. 128GB"),
    ram: str | None = Query(None, description="Android only: RAM value, e.g. 6GB")
):
    return get_colors_by_storage_controller(model_id, None, ram, storage)

@router.get("/GetItemsWithSpec")
def get_items(
    model_id: int = Query(...),
    storage: str = Query(..., description="Storage value, e.g. 128GB"),
    color: str = Query(..., description="Color value, e.g. Just Black"),
    ram: str | None = Query(None, description="Android only: RAM value, e.g. 6GB")
):
    return get_items_controller(
        model_id,
        storage,
        color,
        ram
    )

@router.get("/GetBuybackPrice")
def get_buyback_price(item_code: str = Query(...)):
    return get_buyback_price_controller(item_code)
