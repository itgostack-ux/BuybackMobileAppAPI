from core.database import get_db_connection
from models.device_model import DeviceService


def fetch_device_services():

    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    name,
                    device_service_id,
                    device_service_name,
                    is_check,
                    creation,
                    modified
                FROM `tabDevice Services`
                WHERE IFNULL(is_check,0)=1
                ORDER BY device_service_id
            """)

            rows = cursor.fetchall()

    services = []

    for row in rows:

        services.append(
            DeviceService(
                name=row["name"],
                device_service_id=row["device_service_id"],
                device_service_name=row["device_service_name"],
                is_check=row.get("is_check"),
                creation=row.get("creation"),
                modified=row.get("modified"),
            )
        )

    return services