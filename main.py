from fastapi import FastAPI, HTTPException, Query
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
import os
from dotenv import load_dotenv
from collections import defaultdict

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
                cursor.execute(
                    """
                    SELECT
                        name,
                        device_service_id,
                        device_service_name,
                        is_active,
                        creation,
                        modified
                    FROM `tabDevice Services`
                    WHERE is_active = 1
                    ORDER BY device_service_id
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
# 🔹 CUSTOMERS API (ALL CUSTOMERS)
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
# =================================================
# 🔹 NESTED QUESTION LIST API (FIXED)
# =================================================
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
    
    # =================================================
# 🔹 APPOINTMENT TYPE LIST API
# =================================================
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