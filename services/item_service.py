from repositories.item_repository import *


def response(data):
    return {"success":True,"count":len(data),"data":data}

def get_brands_by_subcategory_service(
    item_group_id=None
):
    return response(
        get_brands_by_subcategory_repo(
            item_group_id
        )
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


def get_attribute_values_service(model_id):
    rows = get_attribute_values_repo(model_id)
    combos = [
        f"{row['ram']}/{row['storage']}" if row.get('ram') else row['storage']
        for row in rows
        if row.get('storage')
    ]
    return response(combos)

import json
from fastapi import HTTPException, status


def _parse_filters(filters: str) -> dict:
    """
    Accepts either:
      - JSON: {"Storage":"128GB","Colour":"Black"}
      - Shorthand: "4GB/64GB/Black"  (always RAM/Storage/Colour, in that order)
    """
    filters = filters.strip()

    # Try JSON first
    try:
        return json.loads(filters)
    except (json.JSONDecodeError, TypeError):
        pass

    # Fall back to shorthand "RAM/Storage/Colour"
    if "/" in filters:
        parts = [p.strip() for p in filters.split("/", 2)]
        if len(parts) == 3 and all(parts):
            return {"RAM": parts[0], "Storage": parts[1], "Colour": parts[2]}

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail='filters must be valid JSON (e.g. {"Storage":"128GB","Colour":"Black"}) '
               'or shorthand "Storage/Colour" (e.g. "128GB/Black")',
    )



def get_items_service(
    item_group_id,
    brand_id,
    model_id,
    filters
):
    parsed_filters = _parse_filters(filters)

    return response(
        get_items_repo(
            item_group_id,
            brand_id,
            model_id,
            parsed_filters
        )
    )

def get_colors_by_storage_service(model_id: int, ram_storage: str):
    ram_storage = ram_storage.strip()

    if "/" in ram_storage:
        ram_value, storage_value = ram_storage.split("/", 1)
        ram_value, storage_value = ram_value.strip(), storage_value.strip()
    else:
        ram_value, storage_value = None, ram_storage

    data = get_colors_by_storage_repo(model_id, storage_value, ram_value)

    return {
        "success": True,
        "message": "Color list fetched successfully",
        "data": data
    }

def get_buyback_price_service(item_code):
    return response(get_buyback_price_repo(item_code))