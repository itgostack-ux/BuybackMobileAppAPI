from repositories.item_repository import *
from fastapi.responses import JSONResponse
from pymysql.err import MySQLError


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
    model_id,
    storage,
    color,
    ram=None
):
    storage_value = _clean_text(storage)
    color_value = _clean_text(color)
    ram_value = _clean_text(ram)

    if not storage_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="storage is required"
        )

    if not color_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="color is required"
        )

    parsed_filters = {
        "Storage": storage_value,
        "Colour": color_value
    }

    if ram_value:
        parsed_filters["RAM"] = ram_value

    try:
        data = get_items_repo(
            model_id,
            parsed_filters
        )
    except MySQLError:
        return _database_error_response()
    except Exception as e:
        if "Can't connect to MySQL" in str(e):
            return _database_error_response()
        raise

    return {
        "success": True,
        "count": len(data),
        "model_id": model_id,
        "ram": ram_value,
        "storage": storage_value,
        "color": color_value,
        "data": data
    }

def _clean_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _database_error_response():
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "message": "Database connection failed. Please check MySQL server is running.",
            "data": []
        }
    )


def get_colors_by_storage_service(
    model_id: int,
    ram_storage: str | None = None,
    ram: str | None = None,
    storage: str | None = None
):
    ram_value = _clean_text(ram)
    storage_value = _clean_text(storage)
    ram_storage = _clean_text(ram_storage)

    if ram_storage and "/" in ram_storage:
        ram_value, storage_value = ram_storage.split("/", 1)
        ram_value, storage_value = _clean_text(ram_value), _clean_text(storage_value)
    elif ram_storage and not storage_value:
        storage_value = ram_storage

    if not storage_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="storage is required. Use storage=128GB or ram_storage=6GB/128GB"
        )

    try:
        data = get_colors_by_storage_repo(model_id, storage_value, ram_value)
    except MySQLError:
        return _database_error_response()
    except Exception as e:
        if "Can't connect to MySQL" in str(e):
            return _database_error_response()
        raise

    return {
        "success": True,
        "message": "Color list fetched successfully",
        "model_id": model_id,
        "ram": ram_value,
        "storage": storage_value,
        "count": len(data),
        "data": data
    }

def get_buyback_price_service(item_code):
    return response(get_buyback_price_repo(item_code))
