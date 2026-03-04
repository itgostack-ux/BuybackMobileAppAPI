from fastapi import FastAPI, HTTPException, Query
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
import os
from dotenv import load_dotenv
from collections import defaultdict
from fastapi import Body, HTTPException
import random
import string
from datetime import datetime
from fastapi import Query, HTTPException

# -------------------------------------------------
# LOAD ENV
# -------------------------------------------------
load_dotenv()

app = FastAPI(title="GoStack FastAPI", version="2.0")

# -------------------------------------------------
# DB CONFIG FROM ENV
# -------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
    "connect_timeout": 5,
}

# -------------------------------------------------
# DB CONNECTION
# -------------------------------------------------
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        yield conn
    finally:
        if conn:
            conn.close()

# -------------------------------------------------
# ROOT
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "FastAPI server is running"}

# -------------------------------------------------
# HEALTH
# -------------------------------------------------
@app.get("/health")
def health():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok")
                result = cursor.fetchone()
        return {"status": "ok", "db": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/GetDeviceServices")
def get_device_services():
    try:
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
                    WHERE IFNULL(is_check, 0) = 1
                    ORDER BY device_service_id
                """)
                rows = cursor.fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        return {"success": False, "error": str(e)}



    # =================================================
# CUSTOMERS API (ALL CUSTOMERS)
# =================================================
@app.get("/Customers")
def get_customers():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        name,
                        customer_name,
                        mobile_no,
                        creation,
                        modified
                    FROM `tabCustomer`
                    ORDER BY name
                    """
                )
                data = cursor.fetchall()

        return {
            "success": True,
            "count": len(data),
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/GetQuestions")
async def get_questions():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    SELECT
                        question_id AS QuestionID,
                        question_text AS QuestionText,
                        question_description AS QuestionDescription,
                        question_type AS QuestionType
                    FROM `tabQuestion Master`
                    WHERE is_active = 1
                    ORDER BY question_id
                """)
                questions = cursor.fetchall()

                if not questions:
                    return {"success": True, "data": {}}

                # Build maps
                question_map = {}
                question_type_map = defaultdict(list)

                for q in questions:
                    q["options"] = []
                   
                    question_map[str(q["QuestionID"])] = q

                question_ids = list(question_map.keys())

                format_strings = ",".join(["%s"] * len(question_ids))

                cursor.execute(f"""
                    SELECT
                        question_id AS QuestionID,
                        option_id AS OptionID,
                        option_text AS OptionText,
                        grade_id AS GradeID,
                        grade_name AS GradeName
                    FROM `tabOption Master`
                    WHERE is_active = 1
                      AND question_id IN ({format_strings})
                    ORDER BY question_id, option_id
                """, tuple(question_ids))

                options = cursor.fetchall()

        # -----------------------------------------
        # Attach options to questions
        # -----------------------------------------
        for opt in options:
            qid = str(opt["QuestionID"])  
            if qid in question_map:
                question_map[qid]["options"].append({
                    "OptionID": opt["OptionID"],
                    "OptionText": opt["OptionText"],
                    "GradeID": opt["GradeID"],
                    "GradeName": opt["GradeName"],
                })

        # -----------------------------------------
        # Group by QuestionType
        # -----------------------------------------
        for q in question_map.values():
            question_type_map[q["QuestionType"]].append({
                "QuestionID": q["QuestionID"],
                "QuestionText": q["QuestionText"],
                "QuestionDescription": q.get("QuestionDescription"),
                "options": q["options"]
            })

        return {"success": True, "data": question_type_map}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
  # =================================================
# 🔹 TEST MASTER LIST API
# =================================================
@app.get("/api/v1/GetTests")
def get_tests():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
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
                    """
                )
                data = cursor.fetchall()

        return {
            "success": True,
            "count": len(data),
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/GetAppointmentTypes")
def get_appointment_types():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
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
                    """
                )
                data = cursor.fetchall()

        return {
            "success": True,
            "count": len(data),
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



    
@app.get("/Customers/{ch_customer_id}")
def get_customer_by_ch_id(ch_customer_id: str):
    try:
        ch_customer_id = ch_customer_id.strip()

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        name AS customer_id,
                        ch_customer_id,
                        customer_name,
                        mobile_no,
                        email_id,
                        customer_type,
                        customer_group,
                        territory,
                        creation,
                        modified,
                        disabled
                    FROM `tabCustomer`
                    WHERE TRIM(LOWER(ch_customer_id)) = TRIM(LOWER(%s))
                    LIMIT 1
                    """,
                    (ch_customer_id,)
                )
                customer = cursor.fetchone()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {
            "success": True,
            "data": customer
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    




def generate_ch_customer_id(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


@app.post("/Customers")
def create_customer(payload: dict = Body(...)):
    try:

        customer_name = (payload.get("customer_name") or "").strip()
        mobile_no = (payload.get("mobile_no") or "").strip()
        email_id = (payload.get("email_id") or "").strip()
        ch_customer_id = (payload.get("ch_customer_id") or "").strip()

        if not customer_name:
            raise HTTPException(status_code=400, detail="customer_name is required")

        if not mobile_no:
            raise HTTPException(status_code=400, detail="mobile_no is required")

    
        customer_name_clean = customer_name.title()   # Proper case
        mobile_no_clean = mobile_no
        email_id_clean = email_id.lower() if email_id else None

        if not ch_customer_id:
            ch_customer_id = generate_ch_customer_id()

        ch_customer_id = ch_customer_id.upper()

        with get_db_connection() as conn:
            with conn.cursor() as cursor:


                cursor.execute(
                    """
                    SELECT name FROM `tabCustomer`
                    WHERE TRIM(mobile_no) = TRIM(%s)
                    LIMIT 1
                    """,
                    (mobile_no_clean,)
                )
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=409,
                        detail="Customer already exists with this mobile number"
                    )

               

                cursor.execute(
                    """
                    SELECT name FROM `tabCustomer`
                    WHERE TRIM(LOWER(ch_customer_id)) = TRIM(LOWER(%s))
                    LIMIT 1
                    """,
                    (ch_customer_id,)
                )
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=409,
                        detail="ch_customer_id already exists"
                    )


                customer_id = customer_name_clean

                # prevent duplicate name PK
                cursor.execute(
                    "SELECT name FROM `tabCustomer` WHERE name = %s LIMIT 1",
                    (customer_id,)
                )
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=409,
                        detail="Customer name already exists"
                    )

        
                now = datetime.utcnow()

                cursor.execute(
                    """
                    INSERT INTO `tabCustomer`
                    (
                        name,
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
                    VALUES (%s,%s,%s,%s,'Company','Individual','All Territories',%s,%s,%s,'Administrator','Administrator',0)
                    """,
                    (
                        customer_id,
                        customer_name_clean,
                        mobile_no_clean,
                        email_id_clean,
                        ch_customer_id,
                        now,
                        now
                    )
                )

            conn.commit()

        return {
            "success": True,
            "message": "Customer created successfully",
            "data": {
                "customer_id": customer_id,
                "ch_customer_id": ch_customer_id
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/GetDeviceItems")
def get_item_groups():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        name,
                        item_group_id,
                        item_group_name,
                        parent_item_group,
                        is_group,
                        lft,
                        rgt,
                        ch_is_active,
                        ch_disabled
                    FROM `tabItem Group`
                    WHERE IFNULL(ch_disabled, 0) = 0
                      AND IFNULL(ch_is_active, 0) = 1
                    ORDER BY lft
                """)
                rows = cursor.fetchall()

        if not rows:
            return {"success": True, "data": []}

        # Build tree
        group_map = {}
        tree = []

        for row in rows:
            row["children"] = []
            group_map[row["name"]] = row

        for row in rows:
            parent = row.get("parent_item_group")

            if parent and parent in group_map:
                group_map[parent]["children"].append(row)
            else:
                tree.append(row)

        return {
            "success": True,
            "count": len(rows),
            "data": tree
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/GetCategories")
def get_categories(item_group_id: str = Query(...)):
    try:
        query = """
            SELECT
                name,
                category_id,
                category_name,
                item_group_id,
                disabled,
                creation,
                modified
            FROM `tabCH Category`
            WHERE IFNULL(disabled,0) = 0
              AND item_group_id = %s
            ORDER BY category_id
        """

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (item_group_id,))
                rows = cursor.fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/GetSubCategories")
def get_sub_categories(
    category_id: str | None = Query(None),
    item_group_id: str | None = Query(None)
):
    try:
        query = """
            SELECT
                name,
                sub_category_id,
                sub_category_name,
                category_id,
                item_group_id,
                prefix,
                hsn_code,
                gst_rate,
                include_manufacturer_in_name,
                include_brand_in_name,
                include_model_in_name,
                disabled,
                creation,
                modified
            FROM `tabCH Sub Category`
            WHERE IFNULL(disabled,0) = 0
        """

        params = []

        if category_id:
            query += " AND category_id = %s"
            params.append(category_id)

        if item_group_id:
            query += " AND item_group_id = %s"
            params.append(item_group_id)

        query += " ORDER BY sub_category_id"

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/GetManufacturers")
def get_manufacturers():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        name,
                        manufacturer_id,
                        short_name,
                        full_name,
                        website,
                        country,
                        logo,
                        notes,
                        creation,
                        modified
                    FROM `tabManufacturer`
                    WHERE IFNULL(ch_disabled, 0) = 0
                      AND IFNULL(ch_is_active, 0) = 1
                    ORDER BY manufacturer_id
                """)
                rows = cursor.fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/GetManufacturerByBrands")
def get_brands(
    manufacturer: str | None = Query(None)
):
    try:
        query = """
            SELECT
                name,
                brand_id,
                brand,
                ch_manufacturer,
                image,
                description,
                creation,
                modified
            FROM `tabBrand`
            WHERE IFNULL(ch_is_active, 0) = 1
        """

        params = []

        if manufacturer:
            query += " AND ch_manufacturer = %s"
            params.append(manufacturer)

        query += " ORDER BY brand_id"

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/GetBrands")
def get_brands():
    try:

        query = """
            SELECT
                name,
                brand_id,
                brand,
                image,
                description,
                ch_manufacturer
            FROM `tabBrand`
            WHERE IFNULL(ch_disabled,0)=0
            AND IFNULL(ch_is_active,1)=1
            ORDER BY brand
        """

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/GetModels")
def get_models(
    item_group_id: int | None = Query(None),
    category_id: int | None = Query(None),
    sub_category_id: int | None = Query(None),
    brand_id: int | None = Query(None)
):
    try:
        query = """
            SELECT
                name,
                model_id,
                model_name,
                manufacturer,
                brand,
                brand_id,
                manufacturer_id,
                sub_category_id,
                category_id,
                item_group_id,
                item_name_preview,
                disabled,
                creation,
                modified
            FROM `tabCH Model`
            WHERE IFNULL(disabled,0) = 0
        """

        params = []

        if item_group_id:
            query += " AND item_group_id = %s"
            params.append(item_group_id)

        if category_id:
            query += " AND category_id = %s"
            params.append(category_id)

        if sub_category_id:
            query += " AND sub_category_id = %s"
            params.append(sub_category_id)

        if brand_id:
            query += " AND brand_id = %s"
            params.append(brand_id)

        query += " ORDER BY model_id"

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/v1/GetAttributes")
def get_attributes():
    try:
        query = """
            SELECT
                name,
                idx,
                attribute_name,
                numeric_values,
                disabled,
                from_range,
                `increment`,
                to_range,
                creation,
                modified
            FROM `tabItem Attribute`
            WHERE IFNULL(disabled,0) = 0
            ORDER BY attribute_name
        """

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/GetModelSpecValues")
def get_model_spec_values(
    item_group_id: int | None = Query(None),
    category_id: int | None = Query(None),
    sub_category_id: int | None = Query(None),
    brand_id: int | None = Query(None),
    model_id: int | None = Query(None)
):
    try:
        query = """
            SELECT
                m.model_id,
                m.model_name,
                s.spec,
                s.spec_value
            FROM `tabCH Model` m
            LEFT JOIN `tabCH Model Spec Value` s
                ON s.parent = m.name
            WHERE IFNULL(m.disabled,0) = 0
        """

        params = []

        if item_group_id:
            query += " AND m.item_group_id = %s"
            params.append(item_group_id)

        if category_id:
            query += " AND m.category_id = %s"
            params.append(category_id)

        if sub_category_id:
            query += " AND m.sub_category_id = %s"
            params.append(sub_category_id)

        if brand_id:
            query += " AND m.brand_id = %s"
            params.append(brand_id)

        if model_id:
            query += " AND m.model_id = %s"
            params.append(model_id)

        query += " ORDER BY m.model_id, s.spec"

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/v1/GetModelWithSpecification")
def get_model_spec_values(
    item_group_id: int | None = Query(None),
    category_id: int | None = Query(None),
    sub_category_id: int | None = Query(None),
    brand_id: int | None = Query(None),
    model_id: int | None = Query(None),
    spec: str | None = Query(None)
):
    try:
        query = """
            SELECT
                m.model_id,
                m.model_name,
                m.brand,
                s.spec,
                s.spec_value
            FROM `tabCH Model` m
            JOIN `tabCH Model Spec Value` s
                ON s.parent = m.name
            WHERE IFNULL(m.disabled,0) = 0
        """

        params = []

        if item_group_id:
            query += " AND m.item_group_id = %s"
            params.append(item_group_id)

        if category_id:
            query += " AND m.category_id = %s"
            params.append(category_id)

        if sub_category_id:
            query += " AND m.sub_category_id = %s"
            params.append(sub_category_id)

        if brand_id:
            query += " AND m.brand_id = %s"
            params.append(brand_id)

        if model_id:
            query += " AND m.model_id = %s"
            params.append(model_id)

        if spec:
            query += " AND s.spec = %s"
            params.append(spec)

        query += " ORDER BY m.model_id, s.spec"

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/GetItems")
def get_items(
    item_group_id: int,
    category_id: int,
    sub_category_id: int,
    brand_id: int,
    model_id: int,
    spec: str,
    spec_value: str
):
    try:
        query = """
        SELECT DISTINCT
            i.item_code,
            i.item_name
        FROM `tabItem` i
        JOIN `tabItem Variant Attribute` a
            ON a.parent = i.name
        WHERE i.disabled = 0
        AND i.ch_item_group_id = %s
        AND i.ch_category_id = %s
        AND i.ch_sub_category_id = %s
        AND i.ch_brand_id = %s
        AND i.ch_model_id = %s
        AND a.attribute = %s
        AND a.attribute_value = %s
        """

        params = (
            item_group_id,
            category_id,
            sub_category_id,
            brand_id,
            model_id,
            spec,
            spec_value
        )

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))