from fastapi import HTTPException
from pymysql.err import MySQLError
from core.database import get_db_connection


def get_tests_repo():

    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    name,
                    test_id,
                    test_name,
                    is_active,
                    creation,
                    modified
                FROM `tabTest Master`
                WHERE is_active = 1
                ORDER BY test_id
            """)

            return cursor.fetchall()


def get_appointment_types_repo():

    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    name,
                    appoinment_id,
                    appoinmnet_type_name,
                    is_active,
                    creation,
                    modified
                FROM `tabAppoinment Type Master`
                WHERE is_active = 1
                ORDER BY appoinment_id
            """)

            return cursor.fetchall()


def get_gofix_stores_repo(
    city=None,
    pincode=None,
    zone=None,
    store_code=None,
    search=None,
    buyback_only=False,
    service_only=False,
    include_inactive=False
):

    query = """
        SELECT
            name,
            store_id,
            store_code,
            store_name,
            company,
            warehouse,
            zone,
            address,
            city,
            state,
            pincode,
            contact_phone,
            custom_latitude,
            custom_longitude,
            latitude,
            longitude,
            google_maps_url,
            is_buyback_enabled,
            is_service_enabled,
            is_retail_enabled,
            is_hub,
            store_status,
            disabled,
            opening_date
        FROM `tabCH Store`
        WHERE UPPER(IFNULL(company, '')) LIKE %s
    """

    params = ["GOFIX%"]

    if not include_inactive:
        query += """
          AND IFNULL(disabled, 0) = 0
          AND IFNULL(store_status, 'Active') = 'Active'
        """

    if buyback_only:
        query += " AND IFNULL(is_buyback_enabled, 0) = 1"

    if service_only:
        query += " AND IFNULL(is_service_enabled, 0) = 1"

    if store_code:
        query += " AND store_code = %s"
        params.append(store_code)

    if pincode:
        query += " AND pincode = %s"
        params.append(pincode)

    if city:
        query += " AND city LIKE %s"
        params.append(f"%{city}%")

    if zone:
        query += " AND zone LIKE %s"
        params.append(f"%{zone}%")

    if search:
        query += " AND (store_name LIKE %s OR address LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY store_name"

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                return cursor.fetchall()

    except MySQLError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed. Please try again."
        )
