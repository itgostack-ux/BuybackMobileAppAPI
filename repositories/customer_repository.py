from datetime import datetime
from fastapi import HTTPException
from core.database import get_db_connection
import uuid

def save_customer_repo(
    customer_id=None,
    customer_name=None,
    mobile_no=None,
    email_id=None,
    disabled=0,
    addresses=None,
    payment_accounts=None
):
    now = datetime.utcnow()

    addresses = addresses or []
    payment_accounts = payment_accounts or []

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                is_update = False

                # ✅ Check existing customer
                if customer_id:
                    cursor.execute("""
                        SELECT name FROM tabCustomer
                        WHERE name=%s LIMIT 1
                    """, (customer_id,))
                    if cursor.fetchone():
                        is_update = True

                # ✅ Duplicate Mobile Check
                if is_update:
                    cursor.execute("""
                        SELECT name FROM tabCustomer
                        WHERE mobile_no=%s AND name!=%s
                        LIMIT 1
                    """, (mobile_no, customer_id))
                else:
                    cursor.execute("""
                        SELECT name FROM tabCustomer
                        WHERE mobile_no=%s
                        LIMIT 1
                    """, (mobile_no,))

                if cursor.fetchone():
                    raise HTTPException(
                        status_code=400,
                        detail="Mobile number already exists"
                    )

                # ========================
                # UPDATE CUSTOMER
                # ========================
                if is_update:

                    cursor.execute("""
                        UPDATE tabCustomer
                        SET customer_name=%s,
                            mobile_no=%s,
                            email_id=%s,
                            disabled=%s,
                            modified=%s
                        WHERE name=%s
                    """, (
                        customer_name,
                        mobile_no,
                        email_id,
                        disabled,
                        now,
                        customer_id
                    ))

                    # ❌ Delete old payment accounts
                    cursor.execute("""
                        DELETE FROM `tabCH Customer Payment Account`
                        WHERE parent=%s
                    """, (customer_id,))

                    # ❌ Delete old dynamic links
                    cursor.execute("""
                        DELETE FROM `tabDynamic Link`
                        WHERE link_name=%s AND link_doctype='Customer'
                    """, (customer_id,))

                    # ❌ Delete old addresses
                    cursor.execute("""
                        DELETE FROM tabAddress
                        WHERE name LIKE %s
                    """, (f"{customer_id}-ADDR-%",))

                # ========================
                # CREATE CUSTOMER
                # ========================
                else:

                    cursor.execute("""
                        SELECT IFNULL(MAX(ch_customer_id),0)+1 AS next_id
                        FROM tabCustomer
                        FOR UPDATE
                    """)
                    next_id = cursor.fetchone()["next_id"]

                    customer_id = f"CUST-{str(next_id).zfill(5)}"

                    cursor.execute("""
                        INSERT INTO tabCustomer (
                            name,
                            naming_series,
                            customer_name,
                            mobile_no,
                            email_id,
                            disabled,
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
                        VALUES (
                            %s,'CUST-.YYYY.-',
                            %s,%s,%s,%s,
                            'Company','Individual','',
                            %s,%s,%s,
                            'Administrator','Administrator',0
                        )
                    """, (
                        customer_id,
                        customer_name,
                        mobile_no,
                        email_id,
                        disabled,
                        next_id,
                        now,
                        now
                    ))

                # ========================
                # ADDRESS INSERT + LINK
                # ========================
                primary_found = False

                for idx, addr in enumerate(addresses, start=1):

                    is_primary = addr.get("is_primary_address", 0)

                    # ✅ Ensure only one primary
                    if is_primary == 1:
                        if primary_found:
                            is_primary = 0
                        primary_found = True

                    address_name = f"{customer_id}-ADDR-{idx}"

                    cursor.execute("""
                        INSERT INTO tabAddress (
                            name,
                            address_title,
                            address_type,
                            address_line1,
                            address_line2,
                            city,
                            state,
                            country,
                            pincode,
                            phone,
                            is_primary_address,
                            creation,
                            modified,
                            owner,
                            modified_by,
                            docstatus
                        )
                        VALUES (
                            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,
                            'Administrator','Administrator',0
                        )
                    """, (
                        address_name,
                        customer_name,
                        addr.get("address_type"),
                        addr.get("address_line1"),
                        addr.get("address_line2"),
                        addr.get("city"),
                        addr.get("state"),
                        addr.get("country"),
                        addr.get("pincode"),
                        mobile_no,
                        is_primary,
                        now,
                        now
                    ))

                    # ✅ Dynamic Link (CRITICAL FIX)
                    cursor.execute("""
                        INSERT INTO `tabDynamic Link` (
                            name,
                            link_doctype,
                            link_name,
                            parent,
                            parenttype,
                            parentfield
                        )
                        VALUES (%s, 'Customer', %s, %s, 'Address', 'links')
                    """, (
                        str(uuid.uuid4())[:10],
                        customer_id,
                        address_name
                    ))

                # ========================
                # PAYMENT ACCOUNTS
                # ========================
                for idx, pay in enumerate(payment_accounts, start=1):

                    cursor.execute("""
                        INSERT INTO `tabCH Customer Payment Account` (
                            name,
                            parent,
                            parentfield,
                            parenttype,
                            idx,
                            account_label,
                            payment_mode,
                            is_default,
                            bank_name,
                            branch,
                            account_holder_name,
                            account_no,
                            ifsc_code,
                            upi_id,
                            creation,
                            modified,
                            owner,
                            modified_by,
                            docstatus
                        )
                        VALUES (
                            %s,%s,
                            'ch_payment_accounts',
                            'Customer',
                            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,
                            'Administrator','Administrator',0
                        )
                    """, (
                        str(uuid.uuid4())[:10],
                        customer_id,
                        idx,
                        pay.get("account_label"),
                        pay.get("payment_mode"),
                        pay.get("is_default"),
                        pay.get("bank_name"),
                        pay.get("branch"),
                        pay.get("account_holder_name"),
                        pay.get("account_no"),
                        pay.get("ifsc_code"),
                        pay.get("upi_id"),
                        now,
                        now
                    ))

            conn.commit()

        return {
            "success": True,
            "customer": customer_id,
            "action": "updated" if is_update else "created"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




















def get_customers_repo(customer_id=None, mobile_no=None):

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                query = """
                    SELECT
                        name,
                        customer_name,
                        mobile_no,
                        email_id,
                        disabled,
                        creation,
                        modified
                    FROM tabCustomer
                    WHERE 1=1
                """

                params = []

                if customer_id:
                    query += " AND name = %s"
                    params.append(customer_id)

                if mobile_no:
                    query += " AND mobile_no = %s"
                    params.append(mobile_no)

                query += " ORDER BY name"

                cursor.execute(query, params)
                customers = cursor.fetchall()

                # Attach Addresses + Payment Accounts
                for customer in customers:

                    # Addresses
                    cursor.execute("""
                        SELECT
                            name,
                            address_title,
                            address_type,
                            address_line1,
                            address_line2,
                            city,
                            state,
                            country,
                            pincode,
                            phone,
                            is_primary_address
                        FROM tabAddress
                        WHERE address_title=%s
                    """, (customer["customer_name"],))

                    customer["addresses"] = cursor.fetchall()

                    # Payment Accounts
                    cursor.execute("""
                        SELECT
                            name,
                            account_label,
                            payment_mode,
                            is_default,
                            bank_name,
                            branch,
                            account_holder_name,
                            account_no,
                            ifsc_code,
                            upi_id
                        FROM `tabCH Customer Payment Account`
                        WHERE parent=%s
                        ORDER BY idx
                    """, (customer["name"],))

                    customer["payment_accounts"] = cursor.fetchall()

        return customers

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_all_customers_repo():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    name,
                    customer_name,
                    mobile_no,
                    email_id,
                    disabled,
                    creation,
                    modified
                FROM tabCustomer
                ORDER BY name
            """)

            customers = cursor.fetchall()

            return customers

def get_customer_by_mobile_repo(mobile_no):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    SELECT
                        ch_customer_id,
                        customer_name,
                        email_id,
                        disabled
                    FROM tabCustomer
                    WHERE mobile_no = %s
                    LIMIT 1
                """, (mobile_no,))

                return cursor.fetchone()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_customer_by_ch_customer_id_repo(ch_customer_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    SELECT
                        c.name,
                        c.ch_customer_id,
                        c.customer_name,
                        c.email_id,
                        c.mobile_no,
                        c.disabled,

                        a.name AS address_id,
                        a.address_title,
                        a.address_type,
                        a.address_line1,
                        a.address_line2,
                        a.city,
                        a.state,
                        a.country,
                        a.pincode,
                        a.phone,
                        a.is_primary_address

                    FROM tabCustomer c

                    LEFT JOIN `tabDynamic Link` dl
                        ON dl.link_name = c.name
                        AND dl.link_doctype = 'Customer'
                        AND dl.parenttype = 'Address'

                    LEFT JOIN tabAddress a
                        ON a.name = dl.parent

                    WHERE c.ch_customer_id = %s
                    ORDER BY a.is_primary_address DESC
                    LIMIT 1
                """, (ch_customer_id,))

                row = cursor.fetchone()

                if not row:
                    return None

                #  Structured response
                return {
                    "name": row["name"],
                    "ch_customer_id": row["ch_customer_id"],
                    "customer_name": row["customer_name"],
                    "email_id": row["email_id"],
                    "mobile_no": row["mobile_no"],
                    "disabled": row["disabled"],
                    "address": {
                        "address_id": row["address_id"],
                        "address_title": row["address_title"],
                        "address_type": row["address_type"],
                        "address_line1": row["address_line1"],
                        "address_line2": row["address_line2"],
                        "city": row["city"],
                        "state": row["state"],
                        "country": row["country"],
                        "pincode": row["pincode"],
                        "phone": row["phone"],
                        "is_primary_address": row["is_primary_address"]
                    } if row["address_id"] else None
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
def get_default_payment_account_repo(ch_customer_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    SELECT
                        c.name,
                        c.ch_customer_id,
                        c.customer_name,

                        pa.name AS payment_id,
                        pa.account_label,
                        pa.payment_mode,
                        pa.is_default,
                        pa.bank_name,
                        pa.branch,
                        pa.account_holder_name,
                        pa.account_no,
                        pa.ifsc_code,
                        pa.upi_id

                    FROM tabCustomer c

                    LEFT JOIN `tabCH Customer Payment Account` pa
                        ON pa.parent = c.name

                    WHERE c.ch_customer_id = %s
                    AND pa.is_default = 1
                    LIMIT 1
                """, (ch_customer_id,))

                return cursor.fetchone()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))