from repositories.master_repository import (
    get_tests_repo,
    get_appointment_types_repo,
    get_gofix_stores_repo
)


def get_tests_service():

    data = get_tests_repo()

    return {
        "success": True,
        "count": len(data),
        "data": data
    }


def get_appointment_types_service():

    data = get_appointment_types_repo()

    return {
        "success": True,
        "count": len(data),
        "data": data
    }


def _clean(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _coordinate(numeric_value, text_value):
    # The numeric latitude/longitude columns are mostly 0 in the ERP.
    # The real position is kept as text in custom_latitude/custom_longitude.
    try:
        number = float(numeric_value or 0)
        if number:
            return number
    except (TypeError, ValueError):
        pass

    try:
        return float(str(text_value).strip()) if text_value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def get_gofix_stores_service(
    city=None,
    pincode=None,
    zone=None,
    store_code=None,
    search=None,
    buyback_only=False,
    service_only=False,
    include_inactive=False
):

    rows = get_gofix_stores_repo(
        city=_clean(city),
        pincode=_clean(pincode),
        zone=_clean(zone),
        store_code=_clean(store_code),
        search=_clean(search),
        buyback_only=bool(buyback_only),
        service_only=bool(service_only),
        include_inactive=bool(include_inactive)
    )

    data = []

    for row in rows:
        data.append({
            "store_id": row.get("store_id"),
            "store_code": row.get("store_code"),
            "store_name": row.get("store_name"),
            "company": row.get("company"),
            "zone": row.get("zone"),
            "address": row.get("address"),
            "city": row.get("city"),
            "state": row.get("state"),
            "pincode": row.get("pincode"),
            "contact_phone": row.get("contact_phone"),
            "latitude": _coordinate(row.get("latitude"), row.get("custom_latitude")),
            "longitude": _coordinate(row.get("longitude"), row.get("custom_longitude")),
            "google_maps_url": row.get("google_maps_url"),
            "warehouse": row.get("warehouse"),
            "is_buyback_enabled": int(row.get("is_buyback_enabled") or 0),
            "is_service_enabled": int(row.get("is_service_enabled") or 0),
            "is_retail_enabled": int(row.get("is_retail_enabled") or 0),
            "is_hub": int(row.get("is_hub") or 0),
            "store_status": row.get("store_status"),
            "disabled": int(row.get("disabled") or 0),
            "opening_date": row.get("opening_date")
        })

    return {
        "success": True,
        "count": len(data),
        "data": data
    }
