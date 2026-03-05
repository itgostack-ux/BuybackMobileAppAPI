from datetime import datetime
from fastapi import HTTPException
from core.database import get_db_connection


def create_customer_repo(customer_name, mobile_no, email_id, address, payment):

    now = datetime.utcnow()

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                # Prevent duplicate mobile
                cursor.execute(
                    "SELECT name FROM tabCustomer WHERE mobile_no=%s LIMIT 1",
                    (mobile_no,)
                )
                existing = cursor.fetchone()

                if existing:
                    return {
                        "success": True,
                        "customer": existing["name"],
                        "message": "Customer already exists"
                    }

                # Generate next ch_customer_id
                cursor.execute("""
                    SELECT IFNULL(MAX(ch_customer_id),0) + 1 AS next_id
                    FROM tabCustomer
                    FOR UPDATE
                """)
                next_id = cursor.fetchone()["next_id"]

                # Generate name
                customer_id = f"CUST-{str(next_id).zfill(5)}"

                # Insert customer
                cursor.execute("""
                    INSERT INTO tabCustomer
                    (
                        name,
                        naming_series,
                        customer_name,
                        mobile_no,
                        email_id,
                        customer_type,
                        customer_group,
                        territory,
                        ch_customer_id,
                        creation,
                        modified,
                        owner,
                        modified_by,
                        docstatus
                    )
                    VALUES
                    (%s,'CUST-.YYYY.-',%s,%s,%s,
                    'Company','Individual','',
                    %s,%s,%s,'Administrator','Administrator',0)
                """,(
                    customer_id,
                    customer_name,
                    mobile_no,
                    email_id,
                    next_id,
                    now,
                    now
                ))

            conn.commit()

        return {
            "success": True,
            "customer": customer_id,
            "ch_customer_id": next_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


def get_customers_repo():

    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    name,
                    customer_name,
                    mobile_no,
                    email_id,
                    creation,
                    modified
                FROM tabCustomer
                ORDER BY name
            """)

            data = cursor.fetchall()

    return data