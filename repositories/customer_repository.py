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

                if customer_id:
                    cursor.execute("""
                        SELECT name FROM tabCustomer
                        WHERE name=%s LIMIT 1
                    """, (customer_id,))
                    if cursor.fetchone():
                        is_update = True

                # Duplicate Mobile Check
                if is_update:
                    cursor.execute("""
                        SELECT name FROM tabCustomer
                        WHERE mobile_no=%s
                        AND name!=%s
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

                # UPDATE
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

                    cursor.execute("""
                        DELETE FROM `tabCH Customer Payment Account`
                        WHERE parent=%s
                    """, (customer_id,))

                    cursor.execute("""
                        DELETE FROM tabAddress
                        WHERE address_title=%s
                    """, (customer_name,))

                # CREATE
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

                # Addresses
                for idx, addr in enumerate(addresses, start=1):
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
                        f"{customer_id}-ADDR-{idx}",
                        customer_name,
                        addr.get("address_type"),
                        addr.get("address_line1"),
                        addr.get("address_line2"),
                        addr.get("city"),
                        addr.get("state"),
                        addr.get("country"),
                        addr.get("pincode"),
                        mobile_no,
                        addr.get("is_primary_address"),
                        now,
                        now
                    ))

                # Payment Accounts
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


def _get_customer(cursor, customer_id):
    cursor.execute("""
        SELECT
            name,
            customer_name,
            mobile_no
        FROM tabCustomer
        WHERE name = %s
        LIMIT 1
    """, (customer_id,))

    return cursor.fetchone()


def _customer_address_exists(cursor, customer_id, address_id):
    cursor.execute("""
        SELECT a.name
        FROM tabAddress a
        JOIN `tabDynamic Link` dl
            ON dl.parent = a.name
        WHERE a.name = %s
          AND dl.link_doctype = 'Customer'
          AND dl.link_name = %s
          AND dl.parenttype = 'Address'
        LIMIT 1
    """, (address_id, customer_id))

    return cursor.fetchone() is not None


def save_customer_address_repo(data):

    now = datetime.utcnow()
    customer_id = data.get("customer_id")
    address_id = data.get("address_id")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                customer = _get_customer(cursor, customer_id)
                if not customer:
                    return {
                        "success": False,
                        "message": "Customer not found",
                        "data": None
                    }

                address_values = (
                    customer["customer_name"],
                    data.get("address_type") or "Billing",
                    data.get("address_line1"),
                    data.get("address_line2"),
                    data.get("city"),
                    data.get("county"),
                    data.get("state"),
                    data.get("country") or "India",
                    data.get("pincode"),
                    data.get("email_id"),
                    data.get("phone") or customer.get("mobile_no"),
                    data.get("is_primary_address") or 0,
                    data.get("is_shipping_address") or 0,
                    data.get("disabled") or 0,
                    data.get("custom_ch_state"),
                    data.get("custom_ch_city"),
                    data.get("custom_ch_pincode"),
                    data.get("custom_area"),
                    now,
                    "Administrator"
                )

                if address_id:
                    if not _customer_address_exists(cursor, customer_id, address_id):
                        return {
                            "success": False,
                            "message": "Address not found for this customer",
                            "data": None
                        }

                    cursor.execute("""
                        UPDATE tabAddress
                        SET address_title = %s,
                            address_type = %s,
                            address_line1 = %s,
                            address_line2 = %s,
                            city = %s,
                            county = %s,
                            state = %s,
                            country = %s,
                            pincode = %s,
                            email_id = %s,
                            phone = %s,
                            is_primary_address = %s,
                            is_shipping_address = %s,
                            disabled = %s,
                            custom_ch_state = %s,
                            custom_ch_city = %s,
                            custom_ch_pincode = %s,
                            custom_area = %s,
                            modified = %s,
                            modified_by = %s
                        WHERE name = %s
                    """, address_values + (address_id,))

                    action = "updated"

                else:
                    address_id = (
                        f"{customer_id}-{data.get('address_type') or 'Address'}-"
                        f"{uuid.uuid4().hex[:8]}"
                    )

                    cursor.execute("""
                        INSERT INTO tabAddress (
                            name,
                            address_title,
                            address_type,
                            address_line1,
                            address_line2,
                            city,
                            county,
                            state,
                            country,
                            pincode,
                            email_id,
                            phone,
                            is_primary_address,
                            is_shipping_address,
                            disabled,
                            custom_ch_state,
                            custom_ch_city,
                            custom_ch_pincode,
                            custom_area,
                            creation,
                            modified,
                            owner,
                            modified_by,
                            docstatus
                        )
                        VALUES (
                            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,'Administrator','Administrator',0
                        )
                    """, (address_id,) + address_values[:-1] + (now,))

                    cursor.execute("""
                        INSERT INTO `tabDynamic Link` (
                            name,
                            parent,
                            parentfield,
                            parenttype,
                            idx,
                            link_doctype,
                            link_name,
                            link_title,
                            creation,
                            modified,
                            owner,
                            modified_by,
                            docstatus
                        )
                        VALUES (
                            %s,%s,'links','Address',1,'Customer',%s,%s,
                            %s,%s,'Administrator','Administrator',0
                        )
                    """, (
                        uuid.uuid4().hex[:10],
                        address_id,
                        customer_id,
                        customer["customer_name"],
                        now,
                        now
                    ))

                    action = "created"

            conn.commit()

        return {
            "success": True,
            "message": f"Address {action} successfully",
            "action": action,
            "address_id": address_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def delete_customer_address_repo(customer_id, address_id):

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                customer = _get_customer(cursor, customer_id)
                if not customer:
                    return {
                        "success": False,
                        "message": "Customer not found"
                    }

                if not _customer_address_exists(cursor, customer_id, address_id):
                    return {
                        "success": False,
                        "message": "Address not found for this customer"
                    }

                cursor.execute("""
                    DELETE FROM `tabDynamic Link`
                    WHERE parent = %s
                      AND parenttype = 'Address'
                      AND link_doctype = 'Customer'
                      AND link_name = %s
                """, (address_id, customer_id))

                cursor.execute("""
                    DELETE FROM tabAddress
                    WHERE name = %s
                """, (address_id,))

            conn.commit()

        return {
            "success": True,
            "message": "Address deleted successfully",
            "address_id": address_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_customer_by_mobile_repo(mobile_no):

    try:
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
                    WHERE mobile_no = %s
                    LIMIT 1
                """, (mobile_no,))

                return cursor.fetchone()

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


def get_customer_addresses_repo(customer_id):

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    SELECT
                        name,
                        customer_name
                    FROM tabCustomer
                    WHERE name = %s
                    LIMIT 1
                """, (customer_id,))

                customer = cursor.fetchone()
                if not customer:
                    return []

                cursor.execute("""
                    SELECT
                        a.name,
                        a.name AS address_id,
                        a.address_title,
                        a.address_type,
                        a.address_line1,
                        a.address_line2,
                        a.city,
                        a.county,
                        a.state,
                        a.country,
                        a.pincode,
                        a.email_id,
                        a.phone,
                        a.is_primary_address,
                        a.is_shipping_address,
                        a.disabled,
                        a.custom_ch_state,
                        a.custom_ch_city,
                        a.custom_ch_pincode,
                        a.custom_area,
                        a.creation,
                        a.modified
                    FROM tabAddress a
                    JOIN `tabDynamic Link` dl
                        ON dl.parent = a.name
                    WHERE dl.link_doctype = 'Customer'
                      AND dl.link_name = %s
                      AND dl.parenttype = 'Address'
                    ORDER BY a.is_primary_address DESC, a.modified DESC
                """, (customer_id,))

                addresses = cursor.fetchall()

                if addresses:
                    return addresses

                cursor.execute("""
                    SELECT
                        name,
                        name AS address_id,
                        address_title,
                        address_type,
                        address_line1,
                        address_line2,
                        city,
                        county,
                        state,
                        country,
                        pincode,
                        email_id,
                        phone,
                        is_primary_address,
                        is_shipping_address,
                        disabled,
                        custom_ch_state,
                        custom_ch_city,
                        custom_ch_pincode,
                        custom_area,
                        creation,
                        modified
                    FROM tabAddress
                    WHERE address_title = %s
                    ORDER BY is_primary_address DESC, modified DESC
                """, (customer["customer_name"],))

                return cursor.fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_customer_orders_appointments_repo(customer_id):

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    SELECT
                        name
                    FROM tabCustomer
                    WHERE name = %s
                    LIMIT 1
                """, (customer_id,))

                if not cursor.fetchone():
                    return {
                        "orders": [],
                        "appointments": []
                    }

                cursor.execute("""
                    SELECT
                        name,
                        order_id,
                        buyback_assessment,
                        settlement_type,
                        customer,
                        customer_name,
                        mobile_no,
                        store,
                        company,
                        status,
                        workflow_state,
                        item,
                        item_name,
                        brand,
                        imei_serial,
                        condition_grade,
                        warranty_status,
                        base_price,
                        total_deductions,
                        final_price,
                        approved_price,
                        payment_status,
                        customer_payout_mode,
                        latest_pickup_appointment,
                        pickup_attempts_count,
                        pickup_completed_at,
                        creation,
                        modified
                    FROM `tabBuyback Order`
                    WHERE customer = %s
                    ORDER BY modified DESC
                """, (customer_id,))

                orders = cursor.fetchall()

                cursor.execute("""
                    SELECT
                        name,
                        appointment_id,
                        status,
                        buyback_order,
                        customer,
                        customer_name,
                        appointment_date,
                        appointment_slot,
                        attempt_number,
                        assigned_to,
                        vendor_partner,
                        vendor_reference,
                        pickup_address,
                        contact_phone,
                        landmark,
                        pincode,
                        completed_at,
                        failure_reason,
                        next_action,
                        reschedule_to,
                        cancelled_at,
                        remarks,
                        customer_notes,
                        creation,
                        modified
                    FROM `tabCH Buyback Pickup Appointment`
                    WHERE customer = %s
                       OR buyback_order IN (
                           SELECT name
                           FROM `tabBuyback Order`
                           WHERE customer = %s
                       )
                    ORDER BY appointment_date DESC, modified DESC
                """, (customer_id, customer_id))

                appointments = cursor.fetchall()

                return {
                    "orders": orders,
                    "appointments": appointments
                }

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
