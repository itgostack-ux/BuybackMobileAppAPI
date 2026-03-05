from fastapi import FastAPI, HTTPException, Query
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
import os
from dotenv import load_dotenv
from collections import defaultdict
# Routers
from routers.buyback_router import router as buyback_router
from routers.customer_router import router as customer_router
from routers.device_router import router as device_router
from routers.question_router import router as question_router
from routers.master_router import router as master_router
from routers.item_router import router as item_router

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


app.include_router(buyback_router)
app.include_router(customer_router)
app.include_router(question_router)
app.include_router(master_router)
app.include_router(device_router)
app.include_router(item_router)


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
    
        
# =================================================
# 🔹 NESTED QUESTION LIST API (FIXED)
# =================================================
@app.get("/api/v1/GetQuestionsBuyback")
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
@app.get("/api/v1/GetTestsDiagonis")
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
    
    # =================================================
# 🔹 APPOINTMENT TYPE LIST API
# =================================================
@app.get("/api/v1/GetAppointmentTypesBuyback")
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


@app.get("/api/v1/GetDeviceItemsBuyback")
def get_item_groups():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        name,
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

@app.get("/api/v1/GetCategoriesBuyback")
def get_categories(
    item_group: str | None = Query(None)
):
    try:
        query = """
            SELECT
                name,
                category_id,
                category_name,
                item_group,
                disabled,
                creation,
                modified
            FROM `tabCH Category`
            WHERE IFNULL(disabled, 0) = 0
        """

        params = []

        # Optional filter
        if item_group:
            query += " AND item_group = %s"
            params.append(item_group)

        query += " ORDER BY category_id"

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

@app.get("/api/v1/GetManufacturersBuyback")
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

@app.get("/api/v1/GetManufacturerByBrandsBuyback")
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


@app.get("/api/v1/GetModelsBuyback")
def get_models(
    sub_category: str | None = Query(None),
    manufacturer: str | None = Query(None),
    brand: str | None = Query(None)
):
    try:
        query = """
            SELECT
                name,
                model_id,
                sub_category,
                manufacturer,
                brand,
                model_name,
                item_name_preview,
                creation,
                modified
            FROM `tabCH Model`
            WHERE IFNULL(disabled, 0) = 0
        """

        params = []

        if sub_category:
            query += " AND sub_category = %s"
            params.append(sub_category)

        if manufacturer:
            query += " AND manufacturer = %s"
            params.append(manufacturer)

        if brand:
            query += " AND brand = %s"
            params.append(brand)

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


    # =================================================
# 🔹 GET CUSTOMER BY CH CUSTOMER ID
# =================================================
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
    