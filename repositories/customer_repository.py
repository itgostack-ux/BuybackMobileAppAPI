from datetime import datetime
from fastapi import HTTPException
from core.database import get_db_connection
from pymysql.err import MySQLError
import uuid


def _flag(value):
    """Coerce None/''/'1'/True into 0 or 1 for NOT NULL tinyint columns."""
    try:
        return 1 if int(value or 0) else 0
    except (TypeError, ValueError):
        return 0


def _insert_customer_address(cursor, customer_id, customer_name, mobile_no, idx, addr, now):
    address_id = f"{customer_id}-ADDR-{idx}"

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
        address_id,
        customer_name,
        addr.get("address_type") or "Billing",
        addr.get("address_line1"),
        addr.get("address_line2"),
        addr.get("city"),
        addr.get("state"),
        addr.get("country") or "India",
        addr.get("pincode"),
        mobile_no,
        _flag(addr.get("is_primary_address")),
        now,
        now
    ))

    # Link the address to the customer the way the ERP does, so that
    # GetAddressByCustomerId / DeleteAddress / SaveAddress can all see it.
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
        customer_name,
        now,
        now
    ))

    return address_id


def _delete_customer_addresses(cursor, customer_id):
    """Remove only the addresses that belong to this customer id (never by name)."""
    cursor.execute("""
        SELECT DISTINCT a.name
        FROM tabAddress a
        LEFT JOIN `tabDynamic Link` dl
            ON dl.parent = a.name
           AND dl.parenttype = 'Address'
           AND dl.link_doctype = 'Customer'
        WHERE dl.link_name = %s
           OR a.name LIKE %s
    """, (customer_id, f"{customer_id}-ADDR-%"))

    names = [row["name"] for row in cursor.fetchall()]

    if not names:
        return 0

    placeholders = ", ".join(["%s"] * len(names))

    cursor.execute(f"""
        DELETE FROM `tabDynamic Link`
        WHERE parenttype = 'Address'
          AND parent IN ({placeholders})
    """, tuple(names))

    cursor.execute(f"""
        DELETE FROM tabAddress
        WHERE name IN ({placeholders})
    """, tuple(names))

    return len(names)


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

    customer_id = (customer_id or "").strip() or None
    customer_name = (customer_name or "").strip() or None
    mobile_no = (mobile_no or "").strip()
    email_id = (email_id or "").strip() or None
    disabled = None if disabled is None else _flag(disabled)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                is_update = False

                existing = None

                if customer_id:
                    cursor.execute("""
                        SELECT name, customer_name, email_id, disabled
                        FROM tabCustomer
                        WHERE name=%s LIMIT 1
                    """, (customer_id,))

                    existing = cursor.fetchone()

                    if not existing:
                        # Never silently create a different customer when the
                        # caller asked to update one that does not exist.
                        raise HTTPException(
                            status_code=404,
                            detail=f"Customer {customer_id} not found"
                        )

                    is_update = True

                # Duplicate mobile check
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

                duplicate = cursor.fetchone()
                if duplicate:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Mobile number already exists for customer {duplicate['name']}"
                    )

                if is_update:
                    # Fields left out of the request keep their current value
                    customer_name = customer_name or existing.get("customer_name") or mobile_no
                    email_id = email_id if email_id is not None else existing.get("email_id")
                    disabled = disabled if disabled is not None else _flag(existing.get("disabled"))

                    cursor.execute("""
                        UPDATE tabCustomer
                        SET customer_name=%s,
                            mobile_no=%s,
                            email_id=%s,
                            disabled=%s,
                            modified=%s,
                            modified_by='Administrator'
                        WHERE name=%s
                    """, (
                        customer_name,
                        mobile_no,
                        email_id,
                        disabled,
                        now,
                        customer_id
                    ))

                    # Only replace child data that the caller actually sent.
                    if payment_accounts is not None:
                        cursor.execute("""
                            DELETE FROM `tabCH Customer Payment Account`
                            WHERE parent=%s
                        """, (customer_id,))

                    if addresses is not None:
                        _delete_customer_addresses(cursor, customer_id)

                else:
                    # Mobile number is the only mandatory field
                    customer_name = customer_name or mobile_no
                    disabled = 0 if disabled is None else disabled

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

                address_ids = []
                for idx, addr in enumerate(addresses or [], start=1):
                    address_ids.append(
                        _insert_customer_address(
                            cursor, customer_id, customer_name, mobile_no, idx, addr, now
                        )
                    )

                for idx, pay in enumerate(payment_accounts or [], start=1):
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
                        uuid.uuid4().hex[:10],
                        customer_id,
                        idx,
                        pay.get("account_label") or "Account",
                        pay.get("payment_mode"),
                        _flag(pay.get("is_default")),
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
            "action": "updated" if is_update else "created",
            "address_ids": address_ids,
            "payment_accounts_saved": len(payment_accounts or [])
        }

    except HTTPException:
        # Keep 404 / 409 as they are instead of rewrapping them as 500
        raise

    except MySQLError as e:
        if getattr(e, "args", [None])[0] in (2003, 2006, 2013, 1045):
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please try again."
            )
        raise HTTPException(
            status_code=500,
            detail="Database error while saving customer"
        )


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


ADDRESS_FIELDS = (
    "address_type", "address_line1", "address_line2", "city", "county", "state",
    "country", "pincode", "email_id", "phone", "is_primary_address",
    "is_shipping_address", "disabled", "custom_ch_state", "custom_ch_city",
    "custom_ch_pincode", "custom_area"
)


class _AddressSaveError(Exception):
    pass


def _clear_other_primary(cursor, customer_id, keep_address_id, column):
    """Only one primary / one shipping address per customer."""
    cursor.execute(f"""
        UPDATE tabAddress a
        JOIN `tabDynamic Link` dl
            ON dl.parent = a.name
           AND dl.parenttype = 'Address'
           AND dl.link_doctype = 'Customer'
           AND dl.link_name = %s
        SET a.{column} = 0
        WHERE a.name != %s
          AND a.{column} = 1
    """, (customer_id, keep_address_id))


def _save_one_address(cursor, customer, customer_id, item, now):
    address_id = (item.get("address_id") or "").strip() or None

    address_values = (
        customer["customer_name"],
        item.get("address_type") or "Billing",
        item.get("address_line1"),
        item.get("address_line2"),
        item.get("city"),
        item.get("county"),
        item.get("state"),
        item.get("country") or "India",
        item.get("pincode"),
        item.get("email_id"),
        item.get("phone") or customer.get("mobile_no"),
        _flag(item.get("is_primary_address")),
        _flag(item.get("is_shipping_address")),
        _flag(item.get("disabled")),
        item.get("custom_ch_state"),
        item.get("custom_ch_city"),
        item.get("custom_ch_pincode"),
        item.get("custom_area"),
        now,
        "Administrator"
    )

    if address_id:
        if not _customer_address_exists(cursor, customer_id, address_id):
            raise _AddressSaveError(f"Address {address_id} not found for this customer")

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
            f"{customer_id}-{item.get('address_type') or 'Address'}-"
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

    if _flag(item.get("is_primary_address")):
        _clear_other_primary(cursor, customer_id, address_id, "is_primary_address")

    if _flag(item.get("is_shipping_address")):
        _clear_other_primary(cursor, customer_id, address_id, "is_shipping_address")

    return {"action": action, "address_id": address_id}


def save_customer_address_repo(data):
    """
    Saves one address (fields given directly in the body) or several
    (data["addresses"] is a list). All addresses are saved in a single
    transaction: if any one of them fails, none are saved.
    """

    now = datetime.utcnow()
    customer_id = data.get("customer_id")
    address_list = data.get("addresses")
    is_bulk = address_list is not None

    if is_bulk:
        items = [item for item in address_list if item]
        if not items:
            return {
                "success": False,
                "message": "addresses list is empty",
                "data": None
            }
    else:
        items = [{key: data.get(key) for key in ADDRESS_FIELDS + ("address_id",)}]

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

                results = []

                for index, item in enumerate(items, start=1):
                    try:
                        saved = _save_one_address(cursor, customer, customer_id, item, now)
                    except _AddressSaveError as exc:
                        conn.rollback()
                        prefix = f"Address {index}: " if is_bulk else ""
                        return {
                            "success": False,
                            "message": f"{prefix}{exc}",
                            "data": None
                        }

                    results.append({"index": index, **saved})

            conn.commit()

        if not is_bulk:
            return {
                "success": True,
                "message": f"Address {results[0]['action']} successfully",
                "action": results[0]["action"],
                "address_id": results[0]["address_id"]
            }

        created = sum(1 for r in results if r["action"] == "created")
        updated = len(results) - created

        return {
            "success": True,
            "message": f"{len(results)} address{'' if len(results) == 1 else 'es'} saved successfully",
            "count": len(results),
            "created": created,
            "updated": updated,
            "data": results
        }

    except MySQLError:
        raise  # handled globally in main.py as a clean 503 / 500


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

    except MySQLError:
        raise  # handled globally in main.py as a clean 503 / 500


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

                # Accept the customer name (CUST-00001), the mobile number,
                # or the numeric ch_customer_id, and resolve to the name.
                numeric_id = int(customer_id) if customer_id.isdigit() else -1

                cursor.execute("""
                    SELECT name
                    FROM tabCustomer
                    WHERE name = %s
                       OR mobile_no = %s
                       OR ch_customer_id = %s
                    ORDER BY
                        CASE
                            WHEN name = %s THEN 0
                            WHEN mobile_no = %s THEN 1
                            ELSE 2
                        END,
                        IFNULL(disabled, 0) ASC,
                        modified DESC
                    LIMIT 1
                """, (customer_id, customer_id, numeric_id, customer_id, customer_id))

                found = cursor.fetchone()

                if not found:
                    return {
                        "customer_id": customer_id,
                        "customer_found": False,
                        "orders": [],
                        "appointments": []
                    }

                customer_id = found["name"]

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
                    "customer_id": customer_id,
                    "customer_found": True,
                    "orders": orders,
                    "appointments": appointments
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# DELETE A CUSTOMER'S BUYBACK ORDERS AND PICKUP APPOINTMENTS
# ==========================================
def _table_columns(cursor, table_name):
    cursor.execute("""
        SELECT column_name AS col
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = %s
    """, (table_name,))

    return {row["col"] for row in cursor.fetchall()}


def _in_clause(values):
    return ", ".join(["%s"] * len(values))


def _delete_child_rows(cursor, doctype, parent_names):
    """
    Removes the child-table rows of the given ERP documents, as the ERP
    itself does when a document is deleted. The table names come from the
    ERP's own field definitions and are checked against information_schema.
    """
    if not parent_names:
        return

    cursor.execute("""
        SELECT options AS child
        FROM tabDocField
        WHERE parent = %s
          AND fieldtype IN ('Table', 'Table MultiSelect')
        UNION
        SELECT options AS child
        FROM `tabCustom Field`
        WHERE dt = %s
          AND fieldtype IN ('Table', 'Table MultiSelect')
    """, (doctype, doctype))

    candidates = ["tab" + row["child"] for row in cursor.fetchall() if row.get("child")]
    if not candidates:
        return

    cursor.execute(f"""
        SELECT table_name AS tbl
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name IN ({_in_clause(candidates)})
    """, tuple(candidates))

    for row in cursor.fetchall():
        table = row["tbl"]
        if "`" in table:
            continue

        cursor.execute(f"""
            DELETE FROM `{table}`
            WHERE parenttype = %s
              AND parent IN ({_in_clause(parent_names)})
        """, (doctype, *parent_names))


def _pickup_done(appointment):
    return (
        (appointment.get("status") or "").strip() == "Completed"
        or bool(appointment.get("completed_at"))
    )


def _order_block_reason(order, orders_with_completed_pickup):
    """Returns why an order must NOT be deleted, or None when it is safe to delete."""
    if int(order.get("docstatus") or 0) != 0:
        return "order is submitted or cancelled in the ERP"

    status = (order.get("status") or "Draft").strip()
    if status != "Draft":
        return f"order status is {status}"

    workflow_state = (order.get("workflow_state") or "Draft").strip()
    if workflow_state != "Draft":
        return f"workflow state is {workflow_state}"

    payment_status = (order.get("payment_status") or "").strip()
    if payment_status.lower() not in ("", "pending", "unpaid"):
        return f"payment status is {payment_status}"

    try:
        if float(order.get("total_paid") or 0) > 0:
            return "a payment is recorded"
    except (TypeError, ValueError):
        pass

    for column, label in (
        ("journal_entry", "a journal entry"),
        ("stock_entry", "a stock entry"),
        ("sales_invoice", "a sales invoice"),
    ):
        if order.get(column):
            return f"{label} is linked"

    if order.get("pickup_completed_at") or order["name"] in orders_with_completed_pickup:
        return "pickup is completed"

    return None


def delete_customer_orders_appointments_repo(customer_id, dry_run=False):
    """
    Deletes the Buyback Orders and Pickup Appointments of one customer.

    Only records that are still open are deleted: Draft orders with no
    payment or accounting link, and appointments whose pickup is not
    completed. Everything else is left alone and reported as skipped.

    With dry_run=True nothing is deleted; the lists show what would be.
    All deletes run in one transaction: if any step fails, nothing is deleted.
    """
    order_wanted = (
        "name", "status", "workflow_state", "docstatus", "payment_status",
        "total_paid", "journal_entry", "stock_entry", "sales_invoice",
        "pickup_completed_at"
    )

    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            # Exact customer id only: a delete must never guess the customer.
            cursor.execute("""
                SELECT name
                FROM tabCustomer
                WHERE name = %s
                LIMIT 1
            """, (customer_id,))

            if not cursor.fetchone():
                return {
                    "customer_found": False,
                    "orders": [],
                    "appointments": [],
                    "skipped_orders": [],
                    "skipped_appointments": []
                }

            order_columns = _table_columns(cursor, "tabBuyback Order")
            appointment_columns = _table_columns(cursor, "tabCH Buyback Pickup Appointment")

            order_select = ", ".join(
                f"`{column}`" for column in order_wanted if column in order_columns
            )

            cursor.execute(f"""
                SELECT {order_select}
                FROM `tabBuyback Order`
                WHERE customer = %s
                ORDER BY creation
            """, (customer_id,))

            orders = cursor.fetchall()

            cursor.execute("""
                SELECT
                    name,
                    status,
                    buyback_order,
                    customer,
                    completed_at
                FROM `tabCH Buyback Pickup Appointment`
                WHERE customer = %s
                   OR buyback_order IN (
                       SELECT name
                       FROM `tabBuyback Order`
                       WHERE customer = %s
                   )
                ORDER BY creation
            """, (customer_id, customer_id))

            appointments = cursor.fetchall()

            orders_with_completed_pickup = {
                appointment["buyback_order"]
                for appointment in appointments
                if _pickup_done(appointment) and appointment.get("buyback_order")
            }

            delete_orders = []
            skipped_orders = []

            for order in orders:
                reason = _order_block_reason(order, orders_with_completed_pickup)
                if reason:
                    skipped_orders.append({"name": order["name"], "reason": reason})
                else:
                    delete_orders.append(order["name"])

            kept_orders = {item["name"] for item in skipped_orders}

            delete_appointments = []
            skipped_appointments = []

            for appointment in appointments:
                if _pickup_done(appointment):
                    reason = "pickup is completed"
                elif appointment.get("buyback_order") in kept_orders:
                    reason = f"its order {appointment['buyback_order']} is not deleted"
                else:
                    reason = None

                if reason:
                    skipped_appointments.append({"name": appointment["name"], "reason": reason})
                else:
                    delete_appointments.append(appointment["name"])

            if not dry_run:

                if delete_appointments:
                    names = tuple(delete_appointments)
                    marks = _in_clause(names)

                    # Clear links held by records that stay
                    if "reschedule_to" in appointment_columns:
                        cursor.execute(f"""
                            UPDATE `tabCH Buyback Pickup Appointment`
                            SET reschedule_to = NULL
                            WHERE reschedule_to IN ({marks})
                        """, names)

                    if "latest_pickup_appointment" in order_columns:
                        cursor.execute(f"""
                            UPDATE `tabBuyback Order`
                            SET latest_pickup_appointment = NULL
                            WHERE latest_pickup_appointment IN ({marks})
                        """, names)

                    _delete_child_rows(cursor, "CH Buyback Pickup Appointment", delete_appointments)

                    cursor.execute(f"""
                        DELETE FROM `tabCH Buyback Pickup Appointment`
                        WHERE name IN ({marks})
                    """, names)

                if delete_orders:
                    names = tuple(delete_orders)
                    marks = _in_clause(names)

                    _delete_child_rows(cursor, "Buyback Order", delete_orders)

                    cursor.execute(f"""
                        DELETE FROM `tabBuyback Order`
                        WHERE name IN ({marks})
                    """, names)

        if not dry_run:
            conn.commit()

    return {
        "customer_found": True,
        "orders": delete_orders,
        "appointments": delete_appointments,
        "skipped_orders": skipped_orders,
        "skipped_appointments": skipped_appointments
    }


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


GOFIX_OPTIONAL_CUSTOMER_COLUMNS = ("ch_customer_id", "ch_membership_id")


def validate_gofix_customer_repo(mobile_no):

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    SELECT column_name AS column_name
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                      AND table_name = 'tabCustomer'
                      AND column_name IN ('ch_customer_id', 'ch_membership_id')
                """)

                existing = {row["column_name"] for row in cursor.fetchall()}

                # Only fixed, whitelisted column names are interpolated here
                extra_sql = "".join(
                    f",\n                        {column}"
                    for column in GOFIX_OPTIONAL_CUSTOMER_COLUMNS
                    if column in existing
                )

                cursor.execute(f"""
                    SELECT
                        name,
                        customer_name,
                        mobile_no,
                        email_id,
                        disabled{extra_sql}
                    FROM tabCustomer
                    WHERE mobile_no = %s
                    ORDER BY IFNULL(disabled, 0) ASC, modified DESC
                    LIMIT 1
                """, (mobile_no,))

                return cursor.fetchone()

    except MySQLError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed. Please try again."
        )


def get_buyback_customers_repo():

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    SELECT
                        c.name AS customer_id,
                        c.customer_name,
                        c.mobile_no,
                        c.email_id,
                        c.ch_customer_id,
                        c.ch_membership_id AS membership_id,
                        IFNULL(c.disabled, 0) AS disabled,
                        IFNULL(a.assessment_count, 0) AS assessment_count,
                        IFNULL(o.order_count, 0) AS order_count,
                        a.latest_assessment,
                        a.latest_assessment_status,
                        a.latest_assessment_price,
                        o.latest_order,
                        o.latest_order_status,
                        o.latest_order_price,
                        GREATEST(
                            IFNULL(a.last_assessment_at, CAST('1000-01-01' AS DATETIME)),
                            IFNULL(o.last_order_at, CAST('1000-01-01' AS DATETIME))
                        ) AS last_activity
                    FROM tabCustomer c
                    LEFT JOIN (
                        SELECT
                            customer,
                            COUNT(*) AS assessment_count,
                            MAX(creation) AS last_assessment_at,
                            SUBSTRING_INDEX(GROUP_CONCAT(name ORDER BY creation DESC), ',', 1) AS latest_assessment,
                            SUBSTRING_INDEX(GROUP_CONCAT(IFNULL(status, '') ORDER BY creation DESC), ',', 1) AS latest_assessment_status,
                            SUBSTRING_INDEX(GROUP_CONCAT(IFNULL(estimated_price, 0) ORDER BY creation DESC), ',', 1) AS latest_assessment_price
                        FROM `tabBuyback Assessment`
                        WHERE IFNULL(customer, '') != ''
                        GROUP BY customer
                    ) a ON a.customer = c.name
                    LEFT JOIN (
                        SELECT
                            customer,
                            COUNT(*) AS order_count,
                            MAX(creation) AS last_order_at,
                            SUBSTRING_INDEX(GROUP_CONCAT(name ORDER BY creation DESC), ',', 1) AS latest_order,
                            SUBSTRING_INDEX(GROUP_CONCAT(IFNULL(status, '') ORDER BY creation DESC), ',', 1) AS latest_order_status,
                            SUBSTRING_INDEX(GROUP_CONCAT(IFNULL(approved_price, 0) ORDER BY creation DESC), ',', 1) AS latest_order_price
                        FROM `tabBuyback Order`
                        WHERE IFNULL(customer, '') != ''
                        GROUP BY customer
                    ) o ON o.customer = c.name
                    WHERE a.customer IS NOT NULL
                       OR o.customer IS NOT NULL
                    ORDER BY last_activity DESC, c.name
                """)

                return cursor.fetchall()

    except MySQLError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed. Please try again."
        )
