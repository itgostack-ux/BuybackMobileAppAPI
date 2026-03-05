from repositories.device_repository import fetch_device_services


def get_device_services_service():

    services = fetch_device_services()

    data = []

    for s in services:

        data.append({
            "name": s.name,
            "device_service_id": s.device_service_id,
            "device_service_name": s.device_service_name,
            "is_check": s.is_check,
            "creation": s.creation,
            "modified": s.modified
        })

    return {
        "success": True,
        "count": len(data),
        "data": data
    }